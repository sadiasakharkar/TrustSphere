import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { getCurrentUser } from '../services/api/auth.service';

const AuthRoleContext = createContext(null);

const defaultSession = {
  name: '',
  username: '',
  email: '',
  role: 'analyst',
  loggedIn: false,
  token: ''
};

const roleViews = {
  employee: {
    sidebar: [
      { href: '/overview', label: 'Overview', icon: 'dashboard' },
      { href: '/monitoring', label: 'My Alerts', icon: 'monitoring' },
      { href: '/email', label: 'Request Analysis', icon: 'upload_file' },
      { href: '/postman', label: 'Postman', icon: 'send' }
    ]
  },
  analyst: {
    sidebar: [
      { href: '/overview', label: 'Overview', icon: 'dashboard' },
      { href: '/incidents', label: 'Incidents', icon: 'assignment' },
      { href: '/monitoring', label: 'Alerts', icon: 'monitoring' },
      { href: '/investigations', label: 'Investigations', icon: 'search_insights' },
      { href: '/threat-graph', label: 'Attack Graph', icon: 'hub' },
      { href: '/playbooks', label: 'Playbooks', icon: 'playlist_add_check' },
      { href: '/analytics', label: 'AI Insights', icon: 'psychology' },
      { href: '/postman', label: 'Postman', icon: 'send' }
    ]
  },
  admin: {
    sidebar: [
      { href: '/overview', label: 'Overview', icon: 'dashboard' },
      { href: '/settings', label: 'System Health', icon: 'monitor_heart' },
      { href: '/detections', label: 'Model Monitoring', icon: 'shield_lock' },
      { href: '/administration', label: 'User Management', icon: 'group' },
      { href: '/monitoring', label: 'Data Sources', icon: 'lan' },
      { href: '/reports', label: 'Compliance Logs', icon: 'fact_check' },
      { href: '/settings', label: 'Configuration', icon: 'settings' },
      { href: '/postman', label: 'Postman', icon: 'send' }
    ]
  }
};

function normalizeRole(role) {
  const normalized = String(role || 'analyst').toLowerCase();
  if (normalized === 'admin') return 'admin';
  if (normalized === 'employee') return 'employee';
  return 'analyst';
}

export function AuthRoleProvider({ children }) {
  const [session, setSession] = useState(defaultSession);
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return undefined;
    const raw = window.localStorage.getItem('trustsphere.session');
    if (!raw) {
      setAuthReady(true);
      return undefined;
    }

    let cancelled = false;

    const hydrateSession = async () => {
      try {
        const parsed = JSON.parse(raw);
        const token = parsed?.token || window.localStorage.getItem('trustsphere.authToken') || '';
        if (!parsed?.username || !token) throw new Error('Missing local auth session.');

        const response = await getCurrentUser(token);
        if (cancelled) return;
        const user = response?.user || {};
        setSession({
          name: user.name || parsed?.name || parsed.username,
          username: user.email || parsed.username,
          email: user.email || parsed?.email || '',
          role: normalizeRole(user.role || parsed.role),
          loggedIn: true,
          token,
        });
      } catch {
        if (!cancelled) {
          setSession(defaultSession);
          window.localStorage.removeItem('trustsphere.session');
          window.localStorage.removeItem('trustsphere.authToken');
          window.localStorage.removeItem('trustsphere.refreshToken');
        }
      } finally {
        if (!cancelled) setAuthReady(true);
      }
    };

    hydrateSession();

    return () => {
      cancelled = true;
    };
  }, []);

  const login = ({ username, role, name = '', token = '', refreshToken = '' }) => {
    const next = {
      name: name?.trim() || username?.trim() || 'secure.operator',
      username: username?.trim() || 'secure.operator',
      email: username?.includes?.('@') ? username.trim() : '',
      role: normalizeRole(role),
      loggedIn: true,
      token
    };
    setSession(next);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('trustsphere.session', JSON.stringify(next));
      if (token) window.localStorage.setItem('trustsphere.authToken', token);
      if (refreshToken) window.localStorage.setItem('trustsphere.refreshToken', refreshToken);
    }
  };

  const logout = () => {
    setSession(defaultSession);
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('trustsphere.session');
      window.localStorage.removeItem('trustsphere.authToken');
      window.localStorage.removeItem('trustsphere.refreshToken');
    }
  };

  const value = useMemo(() => ({
    session,
    role: session.role,
    authReady,
    isAdmin: session.role === 'admin',
    isAnalyst: session.role === 'analyst',
    isEmployee: session.role === 'employee',
    roleView: roleViews[session.role] || roleViews.analyst,
    login,
    logout
  }), [authReady, session]);

  return <AuthRoleContext.Provider value={value}>{children}</AuthRoleContext.Provider>;
}

export function useAuthRole() {
  const ctx = useContext(AuthRoleContext);
  if (!ctx) throw new Error('useAuthRole must be used within AuthRoleProvider');
  return ctx;
}

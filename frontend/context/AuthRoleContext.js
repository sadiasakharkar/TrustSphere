import { createContext, useContext, useEffect, useMemo, useState } from 'react';

const AuthRoleContext = createContext(null);

const defaultSession = {
  name: '',
  username: '',
  email: '',
  role: 'analyst',
  loggedIn: false
};

const roleViews = {
  employee: {
    sidebar: [
      { href: '/overview', label: 'Overview', icon: 'dashboard' },
      { href: '/email', label: 'Request Analysis', icon: 'mail' },
      { href: '/monitoring', label: 'My Alerts', icon: 'monitoring' },
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
      { href: '/analytics', label: 'AI Insights', icon: 'psychology' }
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
      { href: '/settings', label: 'Configuration', icon: 'settings' }
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
    try {
      const parsed = JSON.parse(raw);
      if (parsed?.username) {
        setSession({
          name: parsed?.name || parsed.username,
          username: parsed.username,
          email: parsed?.email || '',
          role: normalizeRole(parsed.role),
          loggedIn: true
        });
      }
    } catch {
      window.localStorage.removeItem('trustsphere.session');
    } finally {
      setAuthReady(true);
    }
  }, []);

  const login = ({ username, role, name = '', email = '' }) => {
    const next = {
      name: name?.trim() || username?.trim() || 'secure.operator',
      username: username?.trim() || 'secure.operator',
      email: email?.trim() || '',
      role: normalizeRole(role),
      loggedIn: true
    };
    setSession(next);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('trustsphere.session', JSON.stringify(next));
    }
  };

  const logout = () => {
    setSession(defaultSession);
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('trustsphere.session');
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

import { createContext, useContext, useEffect, useMemo, useState } from 'react';

const AuthRoleContext = createContext(null);

const defaultSession = {
  name: '',
  username: '',
  role: 'analyst',
  loggedIn: false
};

const roleViews = {
  employee: {
    sidebar: [
      { href: '/overview', label: 'Overview', icon: 'dashboard' },
      { href: '/email', label: 'Email Risk', icon: 'mail' },
      { href: '/monitoring', label: 'Basic Alerts', icon: 'warning' }
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

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const raw = window.localStorage.getItem('trustsphere.session');
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw);
      if (parsed?.username) {
        setSession({
          name: parsed?.name || parsed.username,
          username: parsed.username,
          role: normalizeRole(parsed.role),
          loggedIn: true
        });
      }
    } catch {
      window.localStorage.removeItem('trustsphere.session');
    }
  }, []);

  const login = ({ username, role, name = '', token = '', refreshToken = '' }) => {
    const next = {
      name: name?.trim() || username?.trim() || 'secure.operator',
      username: username?.trim() || 'secure.operator',
      role: normalizeRole(role),
      loggedIn: true
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
    isAdmin: session.role === 'admin',
    isAnalyst: session.role === 'analyst',
    isEmployee: session.role === 'employee',
    roleView: roleViews[session.role] || roleViews.analyst,
    login,
    logout
  }), [session]);

  return <AuthRoleContext.Provider value={value}>{children}</AuthRoleContext.Provider>;
}

export function useAuthRole() {
  const ctx = useContext(AuthRoleContext);
  if (!ctx) throw new Error('useAuthRole must be used within AuthRoleProvider');
  return ctx;
}

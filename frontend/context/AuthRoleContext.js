import { createContext, useContext, useEffect, useMemo, useState } from 'react';

const AuthRoleContext = createContext(null);

const defaultSession = {
  name: '',
  username: '',
  email: '',
  role: 'employee',
  loggedIn: false
};

const roleViews = {
  employee: {
    sidebar: [
      { href: '/overview', label: 'Overview', icon: 'dashboard' },
      { href: '/detections', label: 'Detections', icon: 'shield_lock' },
      { href: '/incidents', label: 'Incidents', icon: 'assignment' }
    ]
  },
  analyst: {
    sidebar: [
      { href: '/overview', label: 'Overview', icon: 'dashboard' },
      { href: '/detections', label: 'Detections', icon: 'shield_lock' },
      { href: '/incidents', label: 'Incidents', icon: 'assignment' },
      { href: '/investigations', label: 'Investigations', icon: 'search_insights' },
      { href: '/playbooks', label: 'Playbooks', icon: 'playlist_add_check' },
      { href: '/response', label: 'Response', icon: 'approval' },
      { href: '/analytics', label: 'Analytics', icon: 'monitoring' }
    ]
  },
  admin: {
    sidebar: [
      { href: '/overview', label: 'Overview', icon: 'dashboard' },
      { href: '/analytics', label: 'Analytics', icon: 'monitoring' },
      { href: '/admin', label: 'Admin', icon: 'settings' }
    ]
  }
};

function normalizeRole(role) {
  const normalized = String(role || 'employee').toLowerCase();
  if (normalized === 'admin') return 'admin';
  if (normalized === 'analyst') return 'analyst';
  return 'employee';
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
      const nextSession = parsed?.username ? {
        name: parsed?.name || parsed.username,
        username: parsed.username,
        email: parsed?.email || '',
        role: normalizeRole(parsed.role),
        loggedIn: true
      } : defaultSession;
      setSession(nextSession);
      window.localStorage.setItem('trustsphere.session', JSON.stringify(nextSession));
    } catch {
      window.localStorage.removeItem('trustsphere.session');
      setSession(defaultSession);
    } finally {
      setAuthReady(true);
    }
  }, []);

  const login = ({ username, role, name = '', email = '', token = '', refreshToken = '' }) => {
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
    roleView: roleViews[session.role] || roleViews.employee,
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

import { createContext, useContext, useEffect, useMemo, useState } from 'react';

const AuthContext = createContext(null);

const defaultSession = {
  name: '',
  username: '',
  role: 'analyst',
  loggedIn: false
};

function normalizeRole(role) {
  return String(role || 'analyst').toLowerCase() === 'admin' ? 'admin' : 'analyst';
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(defaultSession);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const raw = window.localStorage.getItem('trustsphere.session');
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        if (parsed?.role && typeof parsed?.username === 'string') {
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
    }
  }, []);

  const login = ({ username, role }) => {
    const next = {
      name: username?.trim() || 'secure.operator',
      username: username?.trim() || 'secure.operator',
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

  const value = useMemo(
    () => ({
      session,
      isAdmin: session.role === 'admin',
      isAnalyst: session.role === 'analyst',
      login,
      logout
    }),
    [session]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

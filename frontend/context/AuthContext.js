import { createContext, useContext, useEffect, useMemo, useState } from 'react';

const AuthContext = createContext(null);

const defaultSession = {
  username: 'soc.analyst',
  role: 'Analyst',
  loggedIn: false
};

export function AuthProvider({ children }) {
  const [session, setSession] = useState(defaultSession);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const raw = window.localStorage.getItem('trustsphere.session');
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        if (parsed?.role && parsed?.username) {
          setSession({ ...parsed, loggedIn: true });
        }
      } catch {
        window.localStorage.removeItem('trustsphere.session');
      }
    }
  }, []);

  const login = ({ username, role }) => {
    const next = { username: username || 'soc.user', role: role || 'Analyst', loggedIn: true };
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
      isAdmin: session.role === 'Admin',
      isAnalyst: session.role === 'Analyst',
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

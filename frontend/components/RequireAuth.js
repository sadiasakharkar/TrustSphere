import { useRouter } from 'next/router';
import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getDefaultRouteForRole } from '../utils/authRedirects';

export default function RequireAuth({ children, adminOnly = false }) {
  const { session, isAdmin, authReady } = useAuth();
  const router = useRouter();
  const allowedRoles = adminOnly ? ['admin'] : null;

  useEffect(() => {
    if (!authReady) return;
    if (!session.loggedIn) {
      router.replace('/login');
      return;
    }
    if (allowedRoles && !allowedRoles.includes(session.role)) {
      router.replace(getDefaultRouteForRole(session.role));
    }
  }, [allowedRoles, authReady, isAdmin, router, session.loggedIn, session.role]);

  if (!authReady) return null;
  if (!session.loggedIn) return null;
  if (allowedRoles && !allowedRoles.includes(session.role)) return null;

  return children;
}

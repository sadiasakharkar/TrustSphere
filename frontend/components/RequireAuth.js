import { useRouter } from 'next/router';
import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getDefaultRouteForRole } from '../utils/authRedirects';

export default function RequireAuth({ children, adminOnly = false, allowedRoles = null }) {
  const { session, isAdmin, authReady } = useAuth();
  const router = useRouter();
  const resolvedAllowedRoles = adminOnly ? ['admin'] : allowedRoles;

  useEffect(() => {
    if (!authReady) return;
    if (!session.loggedIn) {
      router.replace('/login');
      return;
    }
    if (resolvedAllowedRoles && !resolvedAllowedRoles.includes(session.role)) {
      router.replace(getDefaultRouteForRole(session.role));
    }
  }, [resolvedAllowedRoles, authReady, isAdmin, router, session.loggedIn, session.role]);

  if (!authReady) return null;
  if (!session.loggedIn) return null;
  if (resolvedAllowedRoles && !resolvedAllowedRoles.includes(session.role)) return null;

  return children;
}

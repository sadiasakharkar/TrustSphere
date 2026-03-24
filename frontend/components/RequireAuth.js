import { useRouter } from 'next/router';
import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export default function RequireAuth({ children, adminOnly = false }) {
  const { session, isAdmin } = useAuth();
  const router = useRouter();
  const allowedRoles = adminOnly ? ['admin'] : null;

  useEffect(() => {
    if (!session.loggedIn) {
      router.replace('/login');
      return;
    }
    if (allowedRoles && !allowedRoles.includes(session.role)) {
      router.replace('/overview');
    }
  }, [allowedRoles, isAdmin, router, session.loggedIn, session.role]);

  if (!session.loggedIn) return null;
  if (allowedRoles && !allowedRoles.includes(session.role)) return null;

  return children;
}

import { useRouter } from 'next/router';
import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export default function RequireAuth({ children, adminOnly = false }) {
  const { session, isAdmin } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!session.loggedIn) {
      router.replace('/login');
      return;
    }
    if (adminOnly && !isAdmin) {
      router.replace('/dashboard');
    }
  }, [adminOnly, isAdmin, router, session.loggedIn]);

  if (!session.loggedIn) return null;
  if (adminOnly && !isAdmin) return null;

  return children;
}

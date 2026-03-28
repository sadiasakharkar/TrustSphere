import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import { getDefaultRouteForRole } from '../utils/authRedirects';

export default function RootPage() {
  const router = useRouter();
  const { authReady, session } = useAuth();

  useEffect(() => {
    if (!authReady) return;
    if (session.loggedIn) {
      router.replace(getDefaultRouteForRole(session.role));
      return;
    }
    router.replace('/login');
  }, [authReady, router, session.loggedIn, session.role]);

  return null;
}

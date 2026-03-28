import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function AdminDashboardRoute() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/settings');
  }, [router]);

  return null;
}

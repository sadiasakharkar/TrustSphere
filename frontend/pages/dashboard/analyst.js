import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function AnalystDashboardRoute() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/overview');
  }, [router]);

  return null;
}

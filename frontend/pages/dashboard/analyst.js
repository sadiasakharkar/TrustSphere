import { useEffect } from 'react';
import { useRouter } from 'next/router';
import RequireAuth from '../../components/RequireAuth';

export default function AnalystDashboardPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/overview');
  }, [router]);

  return <RequireAuth>{null}</RequireAuth>;
}

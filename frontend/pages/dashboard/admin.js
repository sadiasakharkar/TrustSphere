import { useEffect } from 'react';
import { useRouter } from 'next/router';
import RequireAuth from '../../components/RequireAuth';

export default function AdminDashboardPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/admin');
  }, [router]);

  return <RequireAuth adminOnly>{null}</RequireAuth>;
}

import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function IncidentsCompatPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/triage');
  }, [router]);
  return null;
}

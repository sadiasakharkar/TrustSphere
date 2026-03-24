import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function AnalyticsCompatPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/investigations');
  }, [router]);
  return null;
}

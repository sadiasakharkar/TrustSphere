import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function PlaybooksCompatPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/response');
  }, [router]);
  return null;
}

import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function ResponseCompatPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/incidents');
  }, [router]);
  return null;
}

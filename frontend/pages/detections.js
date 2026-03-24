import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function DetectionsCompatPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/analytics');
  }, [router]);
  return null;
}

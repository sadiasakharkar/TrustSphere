import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function AdministrationCompatPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/settings');
  }, [router]);
  return null;
}

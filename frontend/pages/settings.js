import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function SettingsCompatPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/administration');
  }, [router]);
  return null;
}

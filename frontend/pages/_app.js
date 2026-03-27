import Head from 'next/head';
import { useEffect, useState } from 'react';
import '../styles/globals.css';
import AppErrorBoundary from '../components/AppErrorBoundary';
import { AuthProvider } from '../context/AuthContext';
import { ThemeProvider } from '../src/design-system/ThemeProvider';

export default function App({ Component, pageProps }) {
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return undefined;

    setOffline(!window.navigator.onLine);
    const markOffline = () => setOffline(true);
    const markOnline = () => setOffline(false);

    window.addEventListener('offline', markOffline);
    window.addEventListener('online', markOnline);

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        // Ignore service worker registration failures so the app still loads normally.
      });
    }

    return () => {
      window.removeEventListener('offline', markOffline);
      window.removeEventListener('online', markOnline);
    };
  }, []);

  return (
    <ThemeProvider>
      <Head>
        <meta name="theme-color" content="#0a0e14" />
        <link rel="manifest" href="/manifest.json" />
      </Head>
      <AppErrorBoundary>
        <AuthProvider>
          {offline ? (
            <div className="offline-banner">
              Offline mode active. TrustSphere is using cached pages and locally saved intelligence.
            </div>
          ) : null}
          <Component {...pageProps} />
        </AuthProvider>
      </AppErrorBoundary>
    </ThemeProvider>
  );
}

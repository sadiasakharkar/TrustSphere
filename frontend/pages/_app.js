import '../styles/globals.css';
import AppErrorBoundary from '../components/AppErrorBoundary';
import { AuthProvider } from '../context/AuthContext';
import { ThemeProvider } from '../src/design-system/ThemeProvider';

export default function App({ Component, pageProps }) {
  return (
    <ThemeProvider>
      <AppErrorBoundary>
        <AuthProvider>
          <Component {...pageProps} />
        </AuthProvider>
      </AppErrorBoundary>
    </ThemeProvider>
  );
}

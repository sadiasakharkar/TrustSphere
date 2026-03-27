import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import { getAuthBaseUrl, loginUser } from '../services/api/auth.service';

export default function LoginPage() {
  const router = useRouter();
  const { login, logout, session, authReady } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('analyst');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const routeRole = String(router.query.role || '').toLowerCase();
    if (['admin', 'analyst', 'employee'].includes(routeRole)) setRole(routeRole);
  }, [router.query.role]);

  useEffect(() => {
    if (!authReady) return;
    if (session.loggedIn) {
      logout();
    }
  }, [authReady]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!email.trim() || !password.trim()) return;

    setSubmitting(true);
    setError('');
    try {
      const response = await loginUser({
        email: email.trim(),
        password,
      });

      const userRole = response?.user?.role || role;
      if (userRole !== role) {
        setError(`This account belongs to ${userRole}. Please choose the correct role and try again.`);
        return;
      }

      login({
        username: response.user?.email || email.trim(),
        name: response.user?.name || email.trim(),
        role: userRole,
        token: response.token || '',
      });
      router.push('/overview');
    } catch (nextError) {
      setError(nextError.message || `Authentication failed. Auth server: ${getAuthBaseUrl()}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--ts-surface)] px-6 py-12">
      <div className="topology-layer" />
      <div className="floating-orb orb-cyan" />
      <div className="floating-orb orb-violet" />
      <main className="relative mx-auto grid min-h-[calc(100vh-6rem)] max-w-6xl items-center gap-12 lg:grid-cols-[1.05fr,0.95fr]">
        <section className="hidden lg:block">
          <h1 className="font-headline text-6xl font-extrabold tracking-tight text-white">TrustSphere</h1>
          <p className="mt-4 max-w-lg text-lg leading-8 soc-text-muted">
            Secure access for administrators, analysts, and employees using real role-based authentication.
          </p>
        </section>
        <section className="soc-glass mx-auto w-full max-w-md p-8 shadow-card">
          <div className="mb-8 flex items-start justify-between gap-4">
            <div>
              <p className="soc-kicker">Sign In</p>
              <h2 className="mt-2 font-headline text-3xl font-extrabold tracking-tight text-white">Access TrustSphere</h2>
              <p className="mt-2 text-sm soc-text-muted">Sign in with your email and password. Choose the role linked to your account.</p>
            </div>
            <button
              type="button"
              className="rounded-full border border-[rgba(140,180,255,0.28)] px-4 py-2 text-sm font-semibold text-white transition hover:border-[rgba(140,180,255,0.5)] hover:bg-[rgba(95,142,229,0.16)]"
              onClick={() => router.push('/signup')}
            >
              Sign up
            </button>
          </div>
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Access role</label>
              <select className="soc-input" value={role} onChange={(event) => setRole(event.target.value)}>
                <option value="admin">Admin</option>
                <option value="analyst">Analyst</option>
                <option value="employee">Employee</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Email</label>
              <input className="soc-input" placeholder="Enter email" value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Password</label>
              <input type="password" className="soc-input" placeholder="Enter password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </div>
            {error ? <p className="text-sm text-[#ffb3ad]">{error}</p> : null}
            <button type="submit" className="soc-btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50" disabled={!email.trim() || !password.trim() || submitting}>
              <span className="material-symbols-outlined text-base">login</span>
              {submitting ? 'Signing in...' : 'Sign in'}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}

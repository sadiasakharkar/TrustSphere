import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../services/api/apiClient';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('analyst');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (String(router.query.role || '').toLowerCase() === 'admin') setRole('admin');
  }, [router.query.role]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!username.trim() || !password.trim()) return;
    setSubmitting(true);
    try {
      const response = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: username.trim(),
          password,
          role,
        }),
      });
      login({
        username: response.data?.user?.name || username.trim(),
        role: response.data?.user?.role || role,
        token: response.data?.access_token || '',
        refreshToken: response.data?.refresh_token || '',
      });
    } catch {
      login({ username: username.trim(), role });
    } finally {
      setSubmitting(false);
    }
    router.push('/overview');
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--ts-surface)] px-6 py-12">
      <div className="topology-layer" />
      <div className="floating-orb orb-cyan" />
      <div className="floating-orb orb-violet" />
      <main className="relative mx-auto grid min-h-[calc(100vh-6rem)] max-w-6xl items-center gap-12 lg:grid-cols-[1.05fr,0.95fr]">
        <section className="hidden lg:block">
          <h1 className="font-headline text-6xl font-extrabold tracking-tight text-white">TrustSphere</h1>
        </section>
        <section className="soc-glass mx-auto w-full max-w-md p-8 shadow-card">
          <div className="mb-8 flex items-start justify-between gap-4">
            <div>
              <p className="soc-kicker">Authorization Required</p>
              <h2 className="mt-2 font-headline text-3xl font-extrabold tracking-tight text-white">Enter the SOC workspace</h2>
              <p className="mt-2 text-sm soc-text-muted">Use a role-based local session. No external identity provider is required for this prototype.</p>
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
                <option value="employee">Employee</option>
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Username</label>
              <input className="soc-input" placeholder="Enter username" value={username} onChange={(event) => setUsername(event.target.value)} />
            </div>
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Password</label>
              <input type="password" className="soc-input" placeholder="Enter password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </div>
            <button type="submit" className="soc-btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50" disabled={!username.trim() || !password.trim() || submitting}>
              <span className="material-symbols-outlined text-base">login</span>
              {submitting ? 'Initializing…' : 'Initialize session'}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../services/api/apiClient';

export default function HomePage() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('analyst');
  const [submitting, setSubmitting] = useState(false);

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
    <div className="relative min-h-screen overflow-hidden bg-[var(--ts-surface-lowest)]">
      <div className="topology-layer" />
      <div className="floating-orb orb-cyan" />
      <div className="floating-orb orb-violet" />
      <main className="relative mx-auto flex min-h-screen max-w-6xl items-center px-5 py-20 sm:px-6">
        <section className="w-full">
          <div className="mx-auto grid max-w-6xl items-center gap-10 lg:grid-cols-[1.1fr,0.9fr]">
            <div className="max-w-2xl">
              <p className="soc-kicker">AI Security Platform</p>
              <h1 className="mt-5 font-headline text-[clamp(3rem,8vw,6.75rem)] font-extrabold leading-[0.96] tracking-[-0.03em] text-white">
                TrustSphere
              </h1>
              <p className="mt-6 max-w-xl text-base leading-8 soc-text-muted">
                An enterprise SOC workspace for monitoring, incident triage, graph-led investigation, response playbooks, and local AI analyst reasoning.
              </p>
            </div>

            <section className="soc-glass mx-auto w-full max-w-xl p-6 sm:p-8">
              <div className="mb-8">
                <p className="soc-kicker">Authorization Required</p>
                <h2 className="mt-3 text-2xl font-semibold tracking-tight text-white">Enter the SOC workspace</h2>
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
                <button
                  type="submit"
                  className="soc-btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={!username.trim() || !password.trim() || submitting}
                >
                  <span className="material-symbols-outlined text-base">login</span>
                  {submitting ? 'Initializing...' : 'Initialize session'}
                </button>
              </form>
              <div className="mt-5 border-t border-[rgba(65,71,85,0.45)] pt-5 text-sm soc-text-muted">
                Need an account?{' '}
                <Link href="/signup" className="font-semibold text-white underline decoration-[rgba(140,180,255,0.45)] underline-offset-4">
                  Sign up
                </Link>
              </div>
            </section>
          </div>
        </section>
      </main>
    </div>
  );
}

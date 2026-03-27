import { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import { getDefaultRouteForRole } from '../utils/authRedirects';

export default function SignupPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('analyst');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!name.trim() || !email.trim() || !password.trim()) return;
    setSubmitting(true);
    login({
      username: email.trim(),
      email: email.trim(),
      role,
      name: name.trim(),
    });
    setSubmitting(false);
    router.push(getDefaultRouteForRole(role));
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
              <p className="soc-kicker">Create Access</p>
              <h2 className="mt-2 font-headline text-3xl font-extrabold tracking-tight text-white">Sign up for the SOC workspace</h2>
              <p className="mt-2 text-sm soc-text-muted">Create a local prototype account, then continue directly into the TrustSphere console.</p>
            </div>
            <button
              type="button"
              className="rounded-full border border-[rgba(140,180,255,0.28)] px-4 py-2 text-sm font-semibold text-white transition hover:border-[rgba(140,180,255,0.5)] hover:bg-[rgba(95,142,229,0.16)]"
              onClick={() => router.push('/login')}
            >
              Log in
            </button>
          </div>
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Full name</label>
              <input className="soc-input" placeholder="Enter your name" value={name} onChange={(event) => setName(event.target.value)} />
            </div>
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Access role</label>
              <select className="soc-input" value={role} onChange={(event) => setRole(event.target.value)}>
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
                <option value="employee">Employee</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Email</label>
              <input className="soc-input" placeholder="Enter email" value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Password</label>
              <input type="password" className="soc-input" placeholder="Create password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </div>
            <button
              type="submit"
              className="soc-btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!name.trim() || !email.trim() || !password.trim() || submitting}
            >
              <span className="material-symbols-outlined text-base">person_add</span>
              {submitting ? 'Creating account...' : 'Create account'}
            </button>
          </form>
          <p className="mt-5 text-sm soc-text-muted">
            Already have access?{' '}
            <button type="button" className="font-semibold text-white underline decoration-[rgba(140,180,255,0.45)] underline-offset-4" onClick={() => router.push('/login')}>
              Log in
            </button>
          </p>
        </section>
      </main>
    </div>
  );
}

import { useState } from 'react';
import { useRouter } from 'next/router';
import { signupUser } from '../services/api/auth.service';

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('analyst');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!name.trim() || !email.trim() || !password.trim()) return;

    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      await signupUser({
        name: name.trim(),
        email: email.trim(),
        password,
        role,
      });
      setSuccess('Account created successfully. You can now sign in.');
      setTimeout(() => router.push(`/login?role=${role}`), 900);
    } catch (nextError) {
      setError(nextError.message || 'Unable to create account.');
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
            Create a real role-based account for admin, analyst, or employee access.
          </p>
        </section>
        <section className="soc-glass mx-auto w-full max-w-md p-8 shadow-card">
          <div className="mb-8 flex items-start justify-between gap-4">
            <div>
              <p className="soc-kicker">Create Access</p>
              <h2 className="mt-2 font-headline text-3xl font-extrabold tracking-tight text-white">Sign up for the SOC workspace</h2>
              <p className="mt-2 text-sm soc-text-muted">Create an account stored in MongoDB with a real role and secure password hash.</p>
            </div>
          </div>
          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Name</label>
              <input className="soc-input" placeholder="Enter your name" value={name} onChange={(event) => setName(event.target.value)} />
            </div>
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Email</label>
              <input className="soc-input" placeholder="Enter your email" value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Role</label>
              <select className="soc-input" value={role} onChange={(event) => setRole(event.target.value)}>
                <option value="admin">Admin</option>
                <option value="analyst">Analyst</option>
                <option value="employee">Employee</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">Password</label>
              <input type="password" className="soc-input" placeholder="Create password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </div>
            {error ? <p className="text-sm text-[#ffb3ad]">{error}</p> : null}
            {success ? <p className="text-sm text-[#8cf0a8]">{success}</p> : null}
            <button
              type="submit"
              className="soc-btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!name.trim() || !email.trim() || !password.trim() || submitting}
            >
              <span className="material-symbols-outlined text-base">person_add</span>
              {submitting ? 'Creating account...' : 'Create account'}
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../services/api/apiClient';

const roleOptions = [
  { value: 'employee', label: 'Employee' },
  { value: 'analyst', label: 'Analyst' },
  { value: 'admin', label: 'Admin' },
];

const postLoginRoute = {
  employee: '/dashboard/employee',
  analyst: '/dashboard/analyst',
  admin: '/dashboard/admin',
};

export default function LoginPage() {
  const router = useRouter();
  const { login, authReady, session } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('employee');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const requestedRole = String(router.query.role || '').toLowerCase();
    if (requestedRole && postLoginRoute[requestedRole]) {
      setRole(requestedRole);
    }
  }, [router.query.role]);

  useEffect(() => {
    if (!authReady || !session.loggedIn) return;
    router.replace(postLoginRoute[session.role] || '/dashboard/employee');
  }, [authReady, router, session.loggedIn, session.role]);

  const isDisabled = useMemo(
    () => !email.trim() || !password.trim() || submitting,
    [email, password, submitting],
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isDisabled) return;

    setSubmitting(true);
    try {
      const response = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: email.trim(),
          password,
          role,
        }),
      });

      login({
        username: response.data?.user?.name || email.trim(),
        name: response.data?.user?.name || email.trim(),
        email: response.data?.user?.email || email.trim(),
        role: response.data?.user?.role || role,
        token: response.data?.access_token || '',
        refreshToken: response.data?.refresh_token || '',
      });
    } catch {
      login({
        username: email.trim(),
        name: email.trim().split('@')[0] || email.trim(),
        email: email.trim(),
        role,
      });
    } finally {
      setSubmitting(false);
    }

    router.push(postLoginRoute[role] || '/dashboard/employee');
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--ts-surface)] px-6 py-10">
      <div className="topology-layer" />
      <main className="relative flex min-h-[calc(100vh-5rem)] items-center justify-center">
        <section className="soc-glass w-full max-w-md rounded-[28px] p-8 shadow-card sm:p-10">
          <div className="mb-8 text-center">
            <p className="font-headline text-3xl font-extrabold tracking-tight text-white">TrustSphere</p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="role" className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">
                Role
              </label>
              <select
                id="role"
                name="role"
                className="soc-input h-14"
                value={role}
                onChange={(event) => setRole(event.target.value)}
              >
                {roleOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="email" className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                inputMode="email"
                className="soc-input h-14"
                placeholder="name@trustsphere.local"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                className="soc-input h-14"
                placeholder="Enter password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </div>

            <button type="submit" className="soc-btn-primary h-14 w-full disabled:cursor-not-allowed disabled:opacity-50" disabled={isDisabled}>
              {submitting ? 'Signing in...' : 'Login'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link href="/signup" className="text-sm font-medium text-[var(--ts-accent)] transition hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ts-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ts-surface-2)]">
              Create account
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}

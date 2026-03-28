import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../services/api/apiClient';

const roleOptions = [
  { value: 'employee', label: 'Employee' },
  { value: 'analyst', label: 'Analyst' },
  { value: 'admin', label: 'Admin' },
];

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function SignupPage() {
  const router = useRouter();
  const { authReady, session } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('employee');
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (authReady && session.loggedIn) {
      router.replace('/overview');
    }
  }, [authReady, router, session.loggedIn]);

  const validate = () => {
    const nextErrors = {};
    if (!name.trim()) nextErrors.name = 'Required';
    if (!email.trim()) nextErrors.email = 'Required';
    else if (!emailPattern.test(email.trim())) nextErrors.email = 'Enter a valid email';
    if (!password.trim()) nextErrors.password = 'Required';
    else if (password.trim().length < 8) nextErrors.password = 'Minimum 8 characters';
    return nextErrors;
  };

  const isDisabled = !name.trim() || !email.trim() || !password.trim() || submitting;

  const handleSubmit = async (event) => {
    event.preventDefault();
    const nextErrors = validate();
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;

    setSubmitting(true);
    try {
      await apiRequest('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          password,
          role,
        }),
        fallbackData: {
          user: {
            name: name.trim(),
            email: email.trim(),
            role,
          },
        },
      });
      router.push(`/login?role=${role}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--ts-surface)] px-6 py-10">
      <div className="topology-layer" />
      <main className="relative flex min-h-[calc(100vh-5rem)] items-center justify-center">
        <section className="soc-glass w-full max-w-md rounded-[28px] p-8 shadow-card sm:p-10">
          <div className="mb-8 text-center">
            <p className="font-headline text-3xl font-extrabold tracking-tight text-white">TrustSphere</p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit} noValidate>
            <div>
              <label htmlFor="name" className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">
                Full Name
              </label>
              <input
                id="name"
                name="name"
                type="text"
                autoComplete="name"
                className="soc-input h-14"
                placeholder="Full name"
                value={name}
                onChange={(event) => {
                  setName(event.target.value);
                  if (errors.name) setErrors((current) => ({ ...current, name: undefined }));
                }}
              />
              {errors.name ? <p className="mt-2 text-xs text-[#ffb3ad]">{errors.name}</p> : null}
            </div>

            <div>
              <label htmlFor="email" className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">
                Work Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                inputMode="email"
                className="soc-input h-14"
                placeholder="name@company.com"
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  if (errors.email) setErrors((current) => ({ ...current, email: undefined }));
                }}
              />
              {errors.email ? <p className="mt-2 text-xs text-[#ffb3ad]">{errors.email}</p> : null}
            </div>

            <div>
              <label htmlFor="password" className="mb-2 block text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.6)]">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                className="soc-input h-14"
                placeholder="Create password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  if (errors.password) setErrors((current) => ({ ...current, password: undefined }));
                }}
              />
              {errors.password ? <p className="mt-2 text-xs text-[#ffb3ad]">{errors.password}</p> : null}
            </div>

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

            <button type="submit" className="soc-btn-primary h-14 w-full disabled:cursor-not-allowed disabled:opacity-50" disabled={isDisabled}>
              {submitting ? 'Creating...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link href="/login" className="text-sm font-medium text-[var(--ts-accent)] transition hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ts-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--ts-surface-2)]">
              Back to login
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}

import { useState } from 'react';
import { useRouter } from 'next/router';

export default function LoginPage() {
  const router = useRouter();
  const [role, setRole] = useState('Analyst');

  const onLogin = () => {
    router.push('/dashboard');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-glow-grid px-4 py-8">
      <div className="card w-full max-w-md p-7">
        <h1 className="text-3xl font-bold text-white">TrustSphere</h1>
        <p className="mt-2 text-sm text-text/80">Cyber Incident Response Dashboard</p>

        <div className="mt-6 space-y-4">
          <input
            className="w-full rounded-lg border border-white/10 bg-bg px-4 py-2 outline-none ring-accent/40 transition focus:ring"
            placeholder="Username"
          />
          <input
            type="password"
            className="w-full rounded-lg border border-white/10 bg-bg px-4 py-2 outline-none ring-accent/40 transition focus:ring"
            placeholder="Password"
          />
          <select
            className="w-full rounded-lg border border-white/10 bg-bg px-4 py-2 outline-none ring-accent/40 transition focus:ring"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <option>Analyst</option>
            <option>Admin</option>
          </select>

          <button className="btn-primary w-full" onClick={onLogin}>
            Login as {role}
          </button>
        </div>

        <button className="mt-4 text-sm text-secondary transition hover:text-accent">Forgot password?</button>
      </div>
    </div>
  );
}

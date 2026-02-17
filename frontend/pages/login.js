import { useState } from 'react';
import { useRouter } from 'next/router';
import Modal from '../components/Modal';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState('soc.analyst');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Analyst');
  const [forgotOpen, setForgotOpen] = useState(false);

  const onLogin = () => {
    login({ username, role, password });
    router.push('/dashboard');
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-glow-grid px-4 py-8">
      <div className="card w-full max-w-md p-7">
        <div className="mb-4 rounded-lg border border-orange-400/30 bg-orange-500/10 p-3 text-xs text-text">
          Air-gapped deployment: no external internet/API dependency in this environment.
        </div>

        <h1 className="text-3xl font-bold text-white">TrustSphere</h1>
        <p className="mt-2 text-sm text-text/80">AI-driven Autonomous Cyber Incident Response System</p>

        <div className="mt-6 space-y-4">
          <input
            className="w-full rounded-lg border border-white/10 bg-bg px-4 py-2 outline-none ring-accent/40 transition focus:ring"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            className="w-full rounded-lg border border-white/10 bg-bg px-4 py-2 outline-none ring-accent/40 transition focus:ring"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
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

        <button className="mt-4 text-sm text-secondary transition hover:text-accent" onClick={() => setForgotOpen(true)}>
          Forgot password?
        </button>
      </div>

      <Modal title="Password Recovery" open={forgotOpen} onClose={() => setForgotOpen(false)}>
        <p className="text-sm text-text/90">Password reset is routed through offline admin workflow in this air-gapped banking environment.</p>
        <div className="mt-4 rounded-lg border border-white/10 bg-bg/60 p-3 text-xs text-text/75">
          Placeholder flow: Submit employee ID {'->'} SOC admin verification {'->'} temporary token issuance.
        </div>
      </Modal>
    </div>
  );
}

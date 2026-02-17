import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Modal from '../components/Modal';
import { useAuth } from '../context/AuthContext';

const modules = [
  'Ingestion: SIEM/EDR/IAM',
  'Normalization + Feature Graph',
  'Anomaly & Correlation Engine',
  'Attack Path Reconstruction',
  'Autonomous Playbook + Narrative'
];

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Analyst');
  const [forgotOpen, setForgotOpen] = useState(false);

  useEffect(() => {
    if (router.query.role === 'Admin') {
      setRole('Admin');
    }
  }, [router.query.role]);

  const onLogin = () => {
    if (!username.trim() || !password.trim()) return;
    login({ username: username.trim(), role, password });
    router.push('/dashboard');
  };

  return (
    <div className="relative min-h-[150vh] bg-bg px-4 py-8">
      <div className="topology-layer" />
      <div className="floating-orb orb-cyan" />
      <div className="floating-orb orb-violet" />

      <div className="relative mx-auto grid w-full max-w-6xl gap-4 lg:grid-cols-5">
        <section className="glass-panel lg:col-span-3">
          <div className="mb-4 inline-flex rounded-full border border-accent/40 bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
            Offline Air-Gapped ACIRS Console
          </div>
          <h1 className="text-4xl font-extrabold leading-tight text-white">TrustSphere</h1>
          <p className="mt-2 max-w-2xl text-sm text-text/85">
            Autonomous Cyber Incident Response for Banking. Built to detect, correlate, and contain threats entirely inside isolated financial networks.
          </p>

          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {modules.map((item, idx) => (
              <div key={item} className="rounded-xl border border-white/10 bg-panel/65 p-3 backdrop-blur">
                <p className="text-xs font-semibold text-secondary">Module {idx + 1}</p>
                <p className="mt-1 text-sm text-white">{item}</p>
              </div>
            ))}
          </div>

          <div className="mt-5 rounded-xl border border-violet/30 bg-violet/10 p-3 text-sm text-text/90">
            Designed for SOC demos: judges can understand ingestion, AI detection, attack-graph fidelity, and playbook generation from UI alone.
          </div>
        </section>

        <section className="glass-panel lg:col-span-2">
          <h2 className="text-2xl font-bold text-white">Secure Login</h2>
          <p className="mt-1 text-xs text-text/75">No internet dependency. Session persists locally for role-based simulation.</p>

          <div className="mt-5 space-y-4">
            <input
              className="w-full rounded-xl border border-white/10 bg-bg/80 px-4 py-2 outline-none ring-accent/40 transition focus:ring"
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <input
              type="password"
              className="w-full rounded-xl border border-white/10 bg-bg/80 px-4 py-2 outline-none ring-accent/40 transition focus:ring"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <select
              className="w-full rounded-xl border border-white/10 bg-bg/80 px-4 py-2 outline-none ring-accent/40 transition focus:ring"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option>Analyst</option>
              <option>Admin</option>
            </select>

            <button className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-50" onClick={onLogin} disabled={!username.trim() || !password.trim()}>
              Access {role} Workspace
            </button>
          </div>

          <button className="mt-4 text-sm text-secondary transition hover:text-accent" onClick={() => setForgotOpen(true)}>
            Forgot password?
          </button>
        </section>
      </div>

      <div className="relative mx-auto mt-8 grid w-full max-w-6xl gap-4 md:grid-cols-3">
        <div className="glass-panel">
          <p className="text-xs uppercase tracking-[0.18em] text-secondary">Transition Layer 01</p>
          <p className="mt-2 text-sm text-text/80">Entity topology visualization and risk stream interpolation.</p>
        </div>
        <div className="glass-panel">
          <p className="text-xs uppercase tracking-[0.18em] text-accent">Transition Layer 02</p>
          <p className="mt-2 text-sm text-text/80">Behavioral drift pipeline with adaptive confidence tuning.</p>
        </div>
        <div className="glass-panel">
          <p className="text-xs uppercase tracking-[0.18em] text-violet-300">Transition Layer 03</p>
          <p className="mt-2 text-sm text-text/80">Narrative intelligence staging for executive response briefings.</p>
        </div>
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

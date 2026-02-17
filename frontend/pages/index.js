import Link from 'next/link';

export default function Home() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-bg">
      <div className="topology-layer" />
      <div className="floating-orb orb-cyan" />
      <div className="floating-orb orb-violet" />

      <main className="relative mx-auto flex min-h-screen max-w-[1600px] flex-col items-center justify-center px-4 text-center">
        <p className="mb-4 rounded-full border border-accent/40 bg-accent/10 px-4 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-accent">
          Autonomous Cyber Incident Response System
        </p>

        <h1 className="hero-word">TRUSTSPHERE</h1>

        <p className="mt-4 max-w-3xl text-sm text-text/80 md:text-base">
          AI-native, fully offline cyber defense platform for banking environments with autonomous detection, correlation, playbook generation, and narrative intelligence.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link href="/login" className="btn-primary px-7 py-3">Login</Link>
          <Link href="/login?role=Admin" className="btn-secondary px-7 py-3">Sign In</Link>
          <a href="#documentation" className="rounded-lg border border-white/20 bg-panel/70 px-7 py-3 font-semibold text-white transition hover:border-accent/60">
            Documentation
          </a>
        </div>
      </main>

      <section id="documentation" className="relative mx-auto max-w-6xl px-4 pb-20">
        <div className="glass-panel">
          <p className="text-xs uppercase tracking-[0.2em] text-secondary">TrustSphere Flow</p>
          <h2 className="mt-2 text-2xl font-bold text-white">How the platform works in an air-gapped SOC</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className="rounded-xl border border-white/10 bg-bg/60 p-3 text-sm text-text/85">1. Ingestion: SIEM, EDR, IAM, banking logs collected locally.</div>
            <div className="rounded-xl border border-white/10 bg-bg/60 p-3 text-sm text-text/85">2. Normalization and feature extraction prepare behavioral vectors.</div>
            <div className="rounded-xl border border-white/10 bg-bg/60 p-3 text-sm text-text/85">3. AI anomaly and correlation engines build attack-path fidelity.</div>
            <div className="rounded-xl border border-white/10 bg-bg/60 p-3 text-sm text-text/85">4. Autonomous playbooks and narrative reports support SOC response.</div>
          </div>
        </div>
      </section>
    </div>
  );
}

import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--ts-surface-lowest)]">
      <div className="topology-layer" />
      <div className="floating-orb orb-cyan" />
      <div className="floating-orb orb-violet" />
      <main className="relative mx-auto flex min-h-screen max-w-7xl flex-col justify-center px-6 py-24">
        <div className="grid items-center gap-12 lg:grid-cols-[1.1fr,0.9fr]">
          <section>
            <p className="soc-kicker">AI Security Platform</p>
            <h1 className="hero-word mt-4 max-w-5xl">TRUSTSPHERE</h1>
            <p className="mt-6 max-w-3xl text-base leading-8 soc-text-muted">
              Enterprise SOC intelligence for banking environments. TrustSphere unifies UEBA, attack graph reconstruction, fraud detectors, and local SOC reasoning inside an offline, explainable security console.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link href="/login" className="soc-btn-primary">Launch console</Link>
              <Link href="/overview" className="soc-btn-secondary">View workspace</Link>
              <a href="#architecture" className="soc-btn-ghost">View architecture</a>
            </div>
          </section>
          <section className="soc-glass p-8 shadow-card">
            <div className="grid gap-4 sm:grid-cols-2">
              {[
                ['Unified Incident Flow', 'Monitoring to triage, investigation, response, and reporting in one command surface.'],
                ['Offline LLM Analyst', 'Local incident intelligence and playbooks with deterministic controls.'],
                ['Graph-Centric Analysis', 'Correlated attacker movement mapped into investigation-ready chains.'],
                ['Enterprise Controls', 'Versioned contracts, strict middleware, and production-mode enforcement.']
              ].map(([title, detail]) => (
                <div key={title} className="soc-panel-muted">
                  <p className="text-sm font-semibold text-white">{title}</p>
                  <p className="mt-2 text-sm leading-6 soc-text-muted">{detail}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
        <section id="architecture" className="mt-20 soc-panel">
          <p className="soc-kicker">Pipeline Architecture</p>
          <h2 className="soc-section-title mt-2">Normalized events to analyst action</h2>
          <div className="mt-6 grid gap-3 lg:grid-cols-5">
            {['Normalize', 'Detect', 'Correlate', 'Reason', 'Respond'].map((step, index) => (
              <div key={step} className="soc-panel-muted">
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.55)]">Stage {index + 1}</p>
                <p className="mt-3 text-sm font-semibold text-white">{step}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

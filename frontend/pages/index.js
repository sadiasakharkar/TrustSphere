import Link from 'next/link';

export default function HomePage() {
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

              <div className="mt-10 flex flex-wrap items-center gap-3">
                <Link href="/login" className="soc-btn-primary">Launch console</Link>
                <Link href="/overview" className="soc-btn-secondary">Enter workspace</Link>
              </div>

              <div className="mt-10 flex flex-wrap gap-2">
                {['UEBA', 'Attack Graph', 'Incident AI', 'Offline Ready'].map((item) => (
                  <span key={item} className="soc-badge border border-[rgba(65,71,85,0.55)] bg-[rgba(16,20,26,0.86)] text-[rgba(223,226,235,0.82)]">
                    {item}
                  </span>
                ))}
              </div>
            </div>

            <section className="soc-glass mx-auto w-full max-w-xl p-6 sm:p-8">
              <div className="border-b border-[rgba(65,71,85,0.45)] pb-5">
                <p className="soc-kicker">Startup Brief</p>
                <h2 className="mt-3 text-2xl font-semibold tracking-tight text-white">Security operations ready</h2>
                <p className="mt-3 text-sm leading-7 soc-text-muted">
                  Launch directly into the command console with the current demo scenario, seeded incidents, and the full analyst workflow connected end to end.
                </p>
              </div>

              <div className="grid gap-3 pt-5 sm:grid-cols-2">
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Environment</p>
                  <p className="mt-3 text-sm font-semibold text-white">Air-gapped demo</p>
                  <p className="mt-1 text-xs soc-text-muted">Frontend-only demo mode with seeded intelligence</p>
                </div>
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Workflow</p>
                  <p className="mt-3 text-sm font-semibold text-white">Monitoring to report</p>
                  <p className="mt-1 text-xs soc-text-muted">Connected incident, graph, playbook, and reporting flow</p>
                </div>
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Detectors</p>
                  <p className="mt-3 text-sm font-semibold text-white">UEBA + fraud suite</p>
                  <p className="mt-1 text-xs soc-text-muted">Email, URL, credential, attachment, and prompt guard models</p>
                </div>
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Analyst entry</p>
                  <p className="mt-3 text-sm font-semibold text-white">Role-based access</p>
                  <p className="mt-1 text-xs soc-text-muted">Admin, Analyst, and Employee entry points via the same SOC shell</p>
                </div>
              </div>
            </section>
          </div>
        </section>
      </main>
    </div>
  );
}

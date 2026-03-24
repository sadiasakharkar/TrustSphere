import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[var(--ts-surface-lowest)]">
      <div className="topology-layer" />
      <div className="floating-orb orb-cyan" />
      <div className="floating-orb orb-violet" />
      <main className="relative mx-auto flex min-h-screen max-w-6xl flex-col items-center justify-center px-6 py-24 text-center">
        <section className="w-full max-w-5xl">
          <p className="soc-kicker">AI Security Platform</p>
          <h1 className="hero-word mt-5">TRUSTSPHERE</h1>
          <p className="mx-auto mt-6 max-w-2xl text-sm leading-7 soc-text-muted sm:text-base sm:leading-8">
            Enterprise SOC intelligence for banking environments, unifying anomaly detection, attack graphs, and analyst reasoning in one offline security console.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            <Link href="/login" className="soc-btn-primary">Launch console</Link>
            <Link href="/overview" className="soc-btn-secondary">View workspace</Link>
          </div>
        </section>
      </main>
    </div>
  );
}

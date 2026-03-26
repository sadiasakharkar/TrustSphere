import Link from 'next/link';
import StatusBadge from './StatusBadge';

export default function LiveResponseFeed({ items = [], streamEvent, title = 'Response queue' }) {
  return (
    <section className="soc-panel">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="soc-kicker">Live Actions</p>
          <h2 className="soc-section-title mt-2">{title}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 soc-text-muted">
            Analysts can see which response step is currently favored for the highest-risk cases and why it stands out.
          </p>
        </div>
        {streamEvent ? (
          <div className="rounded-xl border border-[rgba(173,198,255,0.2)] bg-[rgba(173,198,255,0.08)] px-4 py-3 lg:max-w-[340px]">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#adc6ff]">Latest stream activity</p>
            <p className="mt-2 text-sm font-semibold text-white">{streamEvent.payload?.incident?.title || streamEvent.payload?.title || streamEvent.type}</p>
            <p className="mt-1 text-xs soc-text-muted">Real-time event received from the incident stream.</p>
          </div>
        ) : null}
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-2">
        {items.map((item) => (
          <article key={item.id} className="soc-response-card rounded-2xl border p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-white">{item.title}</p>
                <p className="mt-1 text-xs soc-text-muted">{item.entity}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge tone={item.severity}>{item.severity}</StatusBadge>
                <StatusBadge tone={item.status}>{item.status}</StatusBadge>
              </div>
            </div>
            <div className="mt-4 rounded-xl border border-[rgba(74,225,118,0.16)] bg-[rgba(74,225,118,0.08)] px-4 py-3">
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#4ae176]">Recommended now</p>
              <p className="mt-2 text-sm font-semibold text-white">{item.action}</p>
              <p className="mt-2 text-sm leading-6 soc-text-muted">{item.rationale}</p>
            </div>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs soc-text-muted">Suitability score {item.score}</p>
              <Link href={`/incident/${item.incidentId}`} className="soc-btn-secondary">Open incident</Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

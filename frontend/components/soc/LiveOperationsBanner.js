import StatusBadge from './StatusBadge';
import StatusIndicator from './StatusIndicator';

function relativeLabel(timestamp) {
  if (!timestamp) return 'Awaiting update';
  const diffSeconds = Math.max(0, Math.round((Date.now() - new Date(timestamp).getTime()) / 1000));
  if (diffSeconds < 5) return 'Just now';
  if (diffSeconds < 60) return `${diffSeconds}s ago`;
  const diffMinutes = Math.round(diffSeconds / 60);
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.round(diffMinutes / 60);
  return `${diffHours}h ago`;
}

export default function LiveOperationsBanner({
  title,
  statusLabel,
  statusTone = 'ready',
  updatedAt,
  summary,
  highlight,
  cta
}) {
  return (
    <section className="soc-live-banner overflow-hidden rounded-[20px] border px-5 py-5">
      <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-3xl">
          <div className="flex flex-wrap items-center gap-3">
            <StatusIndicator status={statusLabel} pulse />
            <StatusBadge tone={statusTone}>{summary?.criticalCount || 0} critical</StatusBadge>
            <StatusBadge tone="medium">Updated {relativeLabel(updatedAt)}</StatusBadge>
          </div>
          <h2 className="mt-4 font-headline text-[32px] font-extrabold tracking-tight text-white">{title}</h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 soc-text-muted">
            {highlight}
          </p>
        </div>

        <div className="flex w-full flex-col gap-3 xl:max-w-[360px]">
          <div className="soc-live-highlight rounded-2xl px-4 py-4">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#adc6ff]">Best next move</p>
            <p className="mt-2 text-lg font-semibold text-white">{summary?.topAction?.label || 'Continue guided investigation'}</p>
            <p className="mt-2 text-sm leading-6 soc-text-muted">{summary?.topAction?.rationale || 'The system is watching for enough signal to prioritize a single action.'}</p>
          </div>
          {cta}
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="soc-panel-muted">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Open incidents</p>
          <p className="mt-3 font-headline text-[34px] font-extrabold tracking-tight text-white">{summary?.openCount || 0}</p>
        </div>
        <div className="soc-panel-muted">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Live queue</p>
          <p className="mt-3 font-headline text-[34px] font-extrabold tracking-tight text-white">{summary?.total || 0}</p>
        </div>
        <div className="soc-panel-muted">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Focus incident</p>
          <p className="mt-3 text-sm font-semibold text-white">{summary?.topIncident?.title || 'Waiting for live focus incident'}</p>
        </div>
        <div className="soc-panel-muted">
          <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Latest stream event</p>
          <p className="mt-3 text-sm font-semibold text-white">{summary?.lastEventLabel || 'Awaiting live incident updates'}</p>
        </div>
      </div>
    </section>
  );
}

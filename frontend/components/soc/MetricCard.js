import StatusBadge from './StatusBadge';

export default function MetricCard({ label, value, delta, tone = 'default', helper }) {
  return (
    <div className="soc-panel-muted min-h-[136px]">
      <div className="flex items-start justify-between gap-3">
        <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">{label}</p>
        <StatusBadge tone={tone}>{delta}</StatusBadge>
      </div>
      <p className="mt-4 font-headline text-[40px] font-extrabold tracking-tight text-white">{value}</p>
      {helper ? <p className="mt-2 text-xs soc-text-muted">{helper}</p> : null}
    </div>
  );
}

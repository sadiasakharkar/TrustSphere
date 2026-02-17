import Badge from './Badge';
import Card from './Card';

export default function MetricCard({ label, value, delta, tone = 'info', helper }) {
  return (
    <Card className="min-h-[132px]">
      <p className="text-sm text-text/80">{label}</p>
      <h3 className="mt-2 text-2xl font-bold text-white">{value}</h3>
      <div className="mt-3 flex items-center justify-between gap-2">
        <Badge tone={tone}>{delta}</Badge>
        {helper && <span className="text-xs text-text/60">{helper}</span>}
      </div>
    </Card>
  );
}

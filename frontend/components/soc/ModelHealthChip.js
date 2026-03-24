import SeverityBadge from './SeverityBadge';

export default function ModelHealthChip({ name, status, detail }) {
  return (
    <div className="soc-panel-muted">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-white">{name}</p>
          <p className="mt-1 text-xs soc-text-muted">{detail}</p>
        </div>
        <SeverityBadge level={status}>{status}</SeverityBadge>
      </div>
    </div>
  );
}

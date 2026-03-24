import Link from 'next/link';
import SeverityBadge from './SeverityBadge';

export default function IncidentCard({ incident }) {
  return (
    <div className="soc-panel-muted">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.6)]">{incident.id}</p>
          <h3 className="mt-2 text-base font-semibold text-white">{incident.eventType}</h3>
          <p className="mt-1 text-sm soc-text-muted">{incident.entity} · {incident.affected}</p>
        </div>
        <SeverityBadge level={incident.severity}>{incident.severity}</SeverityBadge>
      </div>
      <div className="mt-4 flex items-center justify-between text-xs soc-text-muted">
        <span>{incident.timestamp}</span>
        <span>Risk {incident.riskScore}</span>
      </div>
      <div className="mt-4 flex items-center justify-between">
        <span className="text-xs font-semibold text-[rgba(223,226,235,0.76)]">{incident.status}</span>
        <Link href={`/incident/${incident.id}`} className="soc-btn-secondary px-3 py-2 text-xs">Open incident</Link>
      </div>
    </div>
  );
}

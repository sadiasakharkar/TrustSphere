import SeverityBadge from './SeverityBadge';

export default function AlertTable({ rows = [], compact = false }) {
  return (
    <div className="overflow-x-auto">
      <table className="soc-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Entity</th>
            <th>Event</th>
            <th>Source</th>
            <th>Severity</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id || row.timestamp} className="soc-table-row">
              <td>{row.timestamp}</td>
              <td className="font-medium text-white">{row.entity}</td>
              <td>{row.eventType}</td>
              <td>{row.source || row.status}</td>
              <td><SeverityBadge level={row.severity}>{row.severity}</SeverityBadge></td>
              <td className={`${compact ? 'text-xs' : 'text-sm'} font-semibold text-white`}>{row.score || row.riskScore}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

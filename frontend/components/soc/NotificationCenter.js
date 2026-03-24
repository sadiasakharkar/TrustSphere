import SeverityBadge from './SeverityBadge';

export default function NotificationCenter({ open, onClose, items = [] }) {
  if (!open) return null;

  return (
    <div className="absolute right-0 top-14 z-50 w-[360px] soc-panel">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="soc-kicker">Notification Center</p>
          <h3 className="soc-section-title text-base">Latest signals</h3>
        </div>
        <button className="soc-btn-ghost px-2 py-1" onClick={onClose}>Close</button>
      </div>
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="soc-panel-muted">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-white">{item.title}</p>
                <p className="mt-1 text-xs leading-5 soc-text-muted">{item.detail}</p>
              </div>
              <SeverityBadge level={item.severity}>{item.severity}</SeverityBadge>
            </div>
            <p className="mt-3 text-[11px] uppercase tracking-[0.14em] text-[rgba(193,198,215,0.55)]">{item.time}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

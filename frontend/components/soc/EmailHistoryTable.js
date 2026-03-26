import StatusBadge from './StatusBadge';

function previewEmail(subject, bodySnippet) {
  const source = subject || bodySnippet || 'No email preview available';
  return source.length > 56 ? source.slice(0, 56) + '...' : source;
}

export default function EmailHistoryTable({ history = [], onClear }) {
  return (
    <section className="soc-panel">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="soc-kicker">Email History</p>
          <h2 className="mt-2 text-base font-semibold text-white">Risk tracking dashboard</h2>
          <p className="mt-2 text-sm leading-6 soc-text-muted">Monitor analyzed email evidence over time, including severity posture and recommended response actions.</p>
        </div>
        <button className="soc-btn-secondary" onClick={onClear}>Clear history</button>
      </div>

      <div className="mt-5 overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-y-3">
          <thead>
            <tr className="text-left text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">
              <th className="px-3 py-2">Time</th>
              <th className="px-3 py-2">Email</th>
              <th className="px-3 py-2">Risk</th>
              <th className="px-3 py-2">Severity</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {history.length ? history.map((item) => (
              <tr key={item.id} className="align-top">
                <td className="rounded-l-2xl bg-[rgba(16,20,26,0.86)] px-3 py-4 text-sm leading-6 soc-text-muted">{item.time}</td>
                <td className="bg-[rgba(16,20,26,0.86)] px-3 py-4 text-sm font-medium text-white">{previewEmail(item.subject, item.bodySnippet)}</td>
                <td className="bg-[rgba(16,20,26,0.86)] px-3 py-4 text-sm text-white">{Number(item.risk || 0).toFixed(2)}</td>
                <td className="bg-[rgba(16,20,26,0.86)] px-3 py-4"><StatusBadge tone={item.severity}>{item.severity}</StatusBadge></td>
                <td className="rounded-r-2xl bg-[rgba(16,20,26,0.86)] px-3 py-4">
                  <div className="flex flex-wrap gap-2">
                    {(item.actions || []).map((action) => (
                      <span key={action} className="soc-badge border border-[rgba(65,71,85,0.55)] bg-[rgba(11,14,19,0.95)] text-[rgba(223,226,235,0.82)]">
                        {action}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            )) : (
              <tr>
                <td colSpan="5" className="rounded-2xl bg-[rgba(16,20,26,0.86)] px-4 py-6 text-sm leading-6 soc-text-muted">
                  No analyzed email evidence has been captured yet for the active overview session.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function normalizeSummary(summary) {
  if (!summary) return null;
  if (typeof summary === 'string') {
    return {
      title: 'Analyst focus',
      description: summary,
      bullets: []
    };
  }
  return {
    title: summary.title || 'Analyst focus',
    description: summary.description || summary.summary || '',
    bullets: Array.isArray(summary.bullets) ? summary.bullets : []
  };
}

export default function RightInsightDrawer({ summary }) {
  const normalized = normalizeSummary(summary);
  if (!normalized) return null;

  return (
    <aside className="soc-insight-drawer">
      <div className="soc-panel sticky top-24">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[#adc6ff]">psychology</span>
          <p className="soc-kicker">AI Insight</p>
        </div>
        <h2 className="mt-3 text-base font-semibold text-white">{normalized.title}</h2>
        {normalized.description ? <p className="mt-3 text-sm leading-6 soc-text-muted">{normalized.description}</p> : null}
        {normalized.bullets.length ? (
          <div className="mt-5 space-y-3">
            {normalized.bullets.map((item) => (
              <div key={item} className="soc-panel-muted">
                <p className="text-sm leading-6 soc-text-muted">{item}</p>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </aside>
  );
}

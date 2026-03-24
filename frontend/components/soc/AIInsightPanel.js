export default function AIInsightPanel({ title = 'AI Insight', children, footer }) {
  return (
    <section className="soc-panel">
      <div className="mb-4 flex items-center gap-2">
        <span className="material-symbols-outlined text-[#adc6ff]">auto_awesome</span>
        <h3 className="soc-section-title">{title}</h3>
      </div>
      <div className="space-y-3 text-sm leading-6 soc-text-muted">{children}</div>
      {footer ? <div className="mt-4 border-t border-[rgba(65,71,85,0.45)] pt-4">{footer}</div> : null}
    </section>
  );
}

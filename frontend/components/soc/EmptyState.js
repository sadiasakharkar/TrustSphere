export default function EmptyState({ title = 'No data available', detail = 'There is nothing to display in this view yet.' }) {
  return (
    <div className="soc-empty">
      <span className="material-symbols-outlined text-3xl text-[rgba(193,198,215,0.48)]">inbox</span>
      <p className="mt-3 text-sm font-semibold text-white">{title}</p>
      <p className="mt-2 max-w-md text-sm soc-text-muted">{detail}</p>
    </div>
  );
}

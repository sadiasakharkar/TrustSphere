export default function EntityPill({ label, type }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-[rgba(65,71,85,0.55)] bg-[rgba(16,20,26,0.85)] px-3 py-1.5 text-xs font-medium text-[rgba(223,226,235,0.82)]">
      <span className="text-[rgba(193,198,215,0.65)]">{type}</span>
      <span>{label}</span>
    </span>
  );
}

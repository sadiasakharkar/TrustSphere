export default function AlertBanner({ title, description, level = 'info' }) {
  const levelMap = {
    info: 'border-accent/40 bg-accent/10',
    warning: 'border-orange-400/40 bg-orange-500/10',
    critical: 'border-red-400/40 bg-red-500/10'
  };

  return (
    <div className={`rounded-xl border px-4 py-3 shadow-card ${levelMap[level]}`}>
      <p className="text-sm font-semibold text-white">{title}</p>
      <p className="mt-1 text-sm text-text/85">{description}</p>
    </div>
  );
}

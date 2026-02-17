export default function MetricCard({ label, value, delta }) {
  const positive = delta.startsWith('+');

  return (
    <div className="card p-4">
      <p className="text-sm text-text/80">{label}</p>
      <h3 className="mt-2 text-2xl font-bold text-white">{value}</h3>
      <span className={`mt-3 inline-block rounded-full px-3 py-1 text-xs ${positive ? 'bg-accent/20 text-accent' : 'bg-secondary/20 text-secondary'}`}>
        {delta}
      </span>
    </div>
  );
}

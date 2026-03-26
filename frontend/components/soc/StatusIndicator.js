export default function StatusIndicator({ status = 'Nominal', pulse = false }) {
  const lower = String(status).toLowerCase();
  const color = lower.includes('ready') || lower.includes('healthy') || lower.includes('nominal') || lower.includes('connected') || lower.includes('live') || lower.includes('active')
    ? 'bg-[#4ae176]'
    : lower.includes('bootstrap') || lower.includes('activating')
      ? 'bg-[#ffb86b]'
    : lower.includes('offline') || lower.includes('error') || lower.includes('critical')
      ? 'bg-[#ff6b6b]'
    : lower.includes('high') || lower.includes('pending') || lower.includes('standby')
      ? 'bg-[#ffb3ad]'
      : 'bg-[#adc6ff]';

  return (
    <div className="inline-flex items-center gap-2">
      <span className={`h-2.5 w-2.5 rounded-full ${color} ${pulse ? 'animate-pulse' : ''}`} />
      <span className="text-xs font-medium text-[rgba(223,226,235,0.76)]">{status}</span>
    </div>
  );
}

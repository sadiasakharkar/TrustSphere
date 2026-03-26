const toneMap = {
  critical: 'bg-[rgba(147,0,10,0.22)] text-[#ffb4ab] border border-[rgba(255,84,81,0.24)]',
  high: 'bg-[rgba(255,179,173,0.12)] text-[#ffb3ad] border border-[rgba(255,179,173,0.2)]',
  medium: 'bg-[rgba(173,198,255,0.12)] text-[#adc6ff] border border-[rgba(173,198,255,0.22)]',
  low: 'bg-[rgba(74,225,118,0.12)] text-[#4ae176] border border-[rgba(74,225,118,0.22)]',
  healthy: 'bg-[rgba(74,225,118,0.12)] text-[#4ae176] border border-[rgba(74,225,118,0.22)]',
  ready: 'bg-[rgba(173,198,255,0.12)] text-[#adc6ff] border border-[rgba(173,198,255,0.22)]',
  open: 'bg-[rgba(255,179,173,0.12)] text-[#ffb3ad] border border-[rgba(255,179,173,0.2)]',
  investigating: 'bg-[rgba(173,198,255,0.12)] text-[#adc6ff] border border-[rgba(173,198,255,0.22)]',
  triaged: 'bg-[rgba(173,198,255,0.12)] text-[#adc6ff] border border-[rgba(173,198,255,0.22)]',
  escalated: 'bg-[rgba(147,0,10,0.22)] text-[#ffb4ab] border border-[rgba(255,84,81,0.24)]',
  contained: 'bg-[rgba(74,225,118,0.12)] text-[#4ae176] border border-[rgba(74,225,118,0.22)]',
  resolved: 'bg-[rgba(74,225,118,0.12)] text-[#4ae176] border border-[rgba(74,225,118,0.22)]',
  default: 'bg-[rgba(38,42,49,0.96)] text-[rgba(223,226,235,0.82)] border border-[rgba(65,71,85,0.55)]'
};

export default function StatusBadge({ tone = 'default', children }) {
  const normalized = String(tone).toLowerCase();
  return <span className={`soc-badge ${toneMap[normalized] || toneMap.default}`}>{children}</span>;
}

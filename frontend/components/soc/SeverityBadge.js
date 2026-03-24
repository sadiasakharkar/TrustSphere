const toneMap = {
  critical: 'bg-[rgba(147,0,10,0.22)] text-[#ffb4ab] border border-[rgba(255,84,81,0.24)]',
  high: 'bg-[rgba(255,179,173,0.12)] text-[#ffb3ad] border border-[rgba(255,179,173,0.2)]',
  medium: 'bg-[rgba(173,198,255,0.12)] text-[#adc6ff] border border-[rgba(173,198,255,0.22)]',
  low: 'bg-[rgba(74,225,118,0.12)] text-[#4ae176] border border-[rgba(74,225,118,0.22)]',
  healthy: 'bg-[rgba(74,225,118,0.12)] text-[#4ae176] border border-[rgba(74,225,118,0.22)]',
  ready: 'bg-[rgba(173,198,255,0.12)] text-[#adc6ff] border border-[rgba(173,198,255,0.22)]'
};

export default function SeverityBadge({ level = 'medium', children }) {
  const normalized = String(level).toLowerCase();
  return <span className={`soc-badge ${toneMap[normalized] || toneMap.medium}`}>{children || level}</span>;
}

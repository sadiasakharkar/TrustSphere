export default function Badge({ tone = 'neutral', children }) {
  const toneClass = {
    neutral: 'bg-white/10 text-text',
    info: 'bg-accent/20 text-accent',
    success: 'bg-secondary/20 text-secondary',
    high: 'bg-orange-500/20 text-orange-300',
    critical: 'bg-red-500/20 text-[#FF4B4B]',
    violet: 'bg-violet/30 text-violet-200'
  }[tone];

  return <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${toneClass}`}>{children}</span>;
}

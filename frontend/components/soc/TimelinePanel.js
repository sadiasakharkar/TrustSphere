export default function TimelinePanel({ items = [], embedded = false }) {
  return (
    <div className={embedded ? 'space-y-4' : 'soc-panel'}>
      <div className="space-y-4">
        {items.map((item, index) => (
          <div key={`${item.time}-${item.title}`} className="relative pl-8">
            <span className="absolute left-0 top-1 h-3 w-3 rounded-full bg-[#adc6ff]" />
            {index < items.length - 1 ? <span className="absolute left-[5px] top-4 h-[calc(100%+0.5rem)] w-px bg-[rgba(65,71,85,0.45)]" /> : null}
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-white">{item.title}</p>
              <span className="text-xs soc-text-muted">{item.time}</span>
            </div>
            <p className="mt-1 text-sm leading-6 soc-text-muted">{item.detail}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

import { useEffect } from 'react';
import Link from 'next/link';

export default function CommandPalette({ open, onClose, actions = [] }) {
  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };
    if (open) window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose, open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70] bg-black/60 p-4 backdrop-blur-sm" onClick={onClose}>
      <div className="mx-auto mt-20 max-w-2xl soc-panel" onClick={(event) => event.stopPropagation()}>
        <div className="flex items-center gap-3 border-b border-[rgba(65,71,85,0.55)] pb-3">
          <span className="material-symbols-outlined text-[#adc6ff]">search</span>
          <input autoFocus className="soc-input border-none bg-transparent px-0 py-0 shadow-none focus:ring-0" placeholder="Search pages, incidents, or entities" />
        </div>
        <div className="mt-4 space-y-2">
          {actions.map((action) => (
            <Link key={action.href} href={action.href} className="flex items-center justify-between rounded-lg px-3 py-3 text-sm hover:bg-[rgba(38,42,49,0.5)]" onClick={onClose}>
              <span className="text-white">{action.label}</span>
              <span className="text-xs soc-text-muted">{action.section}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

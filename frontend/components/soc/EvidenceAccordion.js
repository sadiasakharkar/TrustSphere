import { useState } from 'react';

export default function EvidenceAccordion({ items = [] }) {
  const [openIndex, setOpenIndex] = useState(0);

  return (
    <div className="space-y-3">
      {items.map((item, index) => {
        const open = index === openIndex;
        return (
          <div key={item.title} className="soc-panel-muted">
            <button className="flex w-full items-center justify-between gap-3 text-left" onClick={() => setOpenIndex(open ? -1 : index)}>
              <div>
                <p className="text-sm font-semibold text-white">{item.title}</p>
                <p className="mt-1 text-xs soc-text-muted">Evidence fragment</p>
              </div>
              <span className="material-symbols-outlined text-[rgba(193,198,215,0.7)]">{open ? 'remove' : 'add'}</span>
            </button>
            {open ? <p className="mt-4 text-sm leading-6 soc-text-muted">{item.content}</p> : null}
          </div>
        );
      })}
    </div>
  );
}

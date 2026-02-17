export default function Modal({ title, open, onClose, children }) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 transition-opacity duration-200"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="card w-full max-w-2xl scale-100 p-5 transition-transform duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between gap-3 border-b border-white/10 pb-3">
          <h3 className="text-xl font-bold text-white">{title}</h3>
          <button className="rounded-md border border-white/20 px-2 py-1 text-sm hover:border-accent/60" onClick={onClose}>
            Close
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

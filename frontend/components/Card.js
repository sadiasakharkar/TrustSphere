export default function Card({ title, subtitle, className = '', children, actions, ...props }) {
  return (
    <section className={`soc-panel ${className}`} {...props}>
      {(title || subtitle || actions) && (
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            {title ? <h3 className="text-base font-semibold text-white">{title}</h3> : null}
            {subtitle ? <p className="mt-1 text-sm soc-text-muted">{subtitle}</p> : null}
          </div>
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

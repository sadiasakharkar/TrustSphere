export default function AuditBanner({ title, description }) {
  return (
    <div className="soc-audit-banner">
      <span className="material-symbols-outlined text-[#ffb4ab]">policy_alert</span>
      <div>
        <p className="text-sm font-semibold text-white">{title}</p>
        <p className="mt-1 text-xs text-[rgba(255,218,214,0.82)]">{description}</p>
      </div>
    </div>
  );
}

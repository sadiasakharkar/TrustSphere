export default function AttackGraphPlaceholder() {
  return (
    <div className="card p-4">
      <h3 className="mb-3 text-lg font-semibold text-white">Connected Attack Graph</h3>
      <svg viewBox="0 0 600 240" className="h-52 w-full rounded-lg bg-bg/70 p-2">
        <circle cx="90" cy="120" r="26" fill="#7F5AF0" />
        <text x="70" y="124" fill="#fff" fontSize="12">User</text>

        <circle cx="240" cy="70" r="26" fill="#00FFFF" />
        <text x="222" y="74" fill="#0D1117" fontSize="12">IAM</text>

        <circle cx="240" cy="170" r="26" fill="#4FD1C5" />
        <text x="222" y="174" fill="#0D1117" fontSize="12">EDR</text>

        <circle cx="400" cy="120" r="30" fill="#E53935" />
        <text x="372" y="124" fill="#fff" fontSize="12">Target</text>

        <circle cx="540" cy="120" r="22" fill="#00FFFF" />
        <text x="522" y="124" fill="#0D1117" fontSize="12">SOC</text>

        <line x1="116" y1="112" x2="214" y2="78" stroke="#00FFFF" strokeWidth="2" />
        <line x1="116" y1="128" x2="214" y2="162" stroke="#4FD1C5" strokeWidth="2" />
        <line x1="266" y1="72" x2="370" y2="112" stroke="#7F5AF0" strokeWidth="2" />
        <line x1="266" y1="168" x2="370" y2="128" stroke="#00FFFF" strokeWidth="2" />
        <line x1="430" y1="120" x2="518" y2="120" stroke="#4FD1C5" strokeWidth="2" />
      </svg>
    </div>
  );
}

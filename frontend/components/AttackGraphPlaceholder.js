import Card from './Card';

export default function AttackGraphPlaceholder() {
  return (
    <Card
      title="Correlated Attack Path"
      subtitle="Phishing -> Privilege Escalation -> Lateral Movement -> Data Exfiltration"
    >
      <svg viewBox="0 0 780 250" className="h-56 w-full rounded-lg bg-bg/70 p-2">
        <defs>
          <linearGradient id="pathGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#00FFFF" />
            <stop offset="100%" stopColor="#7F5AF0" />
          </linearGradient>
        </defs>

        <rect x="30" y="90" width="150" height="72" rx="12" fill="#161B22" stroke="#00FFFF" />
        <text x="47" y="120" fill="#E6EDF3" fontSize="12">Initial Access</text>
        <text x="47" y="140" fill="#00FFFF" fontSize="12">Phishing Link</text>

        <rect x="220" y="90" width="150" height="72" rx="12" fill="#161B22" stroke="#4FD1C5" />
        <text x="238" y="120" fill="#E6EDF3" fontSize="12">Privilege Esc.</text>
        <text x="238" y="140" fill="#4FD1C5" fontSize="12">Token Abuse</text>

        <rect x="410" y="90" width="150" height="72" rx="12" fill="#161B22" stroke="#7F5AF0" />
        <text x="427" y="120" fill="#E6EDF3" fontSize="12">Lateral Move</text>
        <text x="427" y="140" fill="#7F5AF0" fontSize="12">SMB Pivot</text>

        <rect x="600" y="90" width="150" height="72" rx="12" fill="#161B22" stroke="#FF4B4B" />
        <text x="622" y="120" fill="#E6EDF3" fontSize="12">Objective</text>
        <text x="622" y="140" fill="#FF4B4B" fontSize="12">Data Exfiltration</text>

        <line x1="180" y1="126" x2="220" y2="126" stroke="url(#pathGrad)" strokeWidth="4" />
        <line x1="370" y1="126" x2="410" y2="126" stroke="url(#pathGrad)" strokeWidth="4" />
        <line x1="560" y1="126" x2="600" y2="126" stroke="url(#pathGrad)" strokeWidth="4" />
      </svg>
    </Card>
  );
}

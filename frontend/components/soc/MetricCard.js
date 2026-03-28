import StatusBadge from './StatusBadge';

function normalizeRole(role) {
  if (role === 'analyst') return 'analyst';
  if (role === 'admin') return 'executive';
  return 'manager';
}

function getMetricTooltip(label, role) {
  const view = normalizeRole(role);
  const copy = {
    'suspicious logins': {
      analyst: [
        'Shows logins that do not match normal employee patterns.',
        'This helps catch account misuse early.',
        'Review activity details to confirm the user identity.',
      ],
      manager: [
        'Shows logins that differ from normal staff behavior.',
        'This matters because unusual access can raise bank risk.',
        'Check alerts if a review or approval is needed.',
      ],
      executive: [
        'Shows unusual login activity across the bank.',
        'It highlights possible exposure to account misuse.',
        'No action unless the volume or severity rises.',
      ],
    },
    'phishing emails detected': {
      analyst: [
        'Shows emails flagged as possible impersonation or fraud.',
        'This helps protect employee accounts and customer data.',
        'Open alerts to verify and contain the risk.',
      ],
      manager: [
        'Shows emails that may be trying to mislead staff.',
        'This matters because email fraud can lead to losses and disruption.',
        'Review pending alerts if team action is required.',
      ],
      executive: [
        'Shows the level of suspicious email activity.',
        'It reflects pressure on staff and overall control strength.',
        'No action unless the trend keeps rising.',
      ],
    },
    'behavior anomalies': {
      analyst: [
        'Shows employees acting outside their usual patterns.',
        'This can point to compromised access or misuse.',
        'Investigate before deciding whether to escalate.',
      ],
      manager: [
        'Shows staff activity that falls outside normal behavior.',
        'This matters because unusual actions can increase operational risk.',
        'Review if a decision or follow-up is needed.',
      ],
      executive: [
        'Shows changes in normal employee behavior across the bank.',
        'It helps indicate whether control risk is growing.',
        'No action unless repeated patterns appear.',
      ],
    },
    'high risk incidents': {
      analyst: [
        'Shows incidents with strong signs of harmful activity.',
        'These matter because they may need fast containment.',
        'Prioritize review and escalate when confirmed.',
      ],
      manager: [
        'Shows the most serious security events awaiting attention.',
        'This matters because delays can raise business risk.',
        'Make a prompt decision to reduce exposure.',
      ],
      executive: [
        'Shows the bank’s most serious active security events.',
        'It reflects immediate operational and financial exposure.',
        'Priority attention is recommended.',
      ],
    },
    'ai risk score': {
      analyst: [
        'Shows how likely the activity is to be harmful.',
        'It helps you rank what to investigate first.',
        'Use it as guidance, not the final decision.',
      ],
      manager: [
        'Shows AI guidance on how serious an alert may be.',
        'This matters because it supports faster decisions.',
        'Use it to support approval or escalation choices.',
      ],
      executive: [
        'Shows AI guidance on current security risk levels.',
        'It helps summarize where attention may be needed.',
        'Use it for context, not as a final judgment.',
      ],
    },
    'payment fraud alert': {
      analyst: [
        'Shows a transaction flagged for unusual approval or transfer behavior.',
        'This helps reduce the chance of financial loss.',
        'Review the evidence before recommending action.',
      ],
      manager: [
        'Shows a payment that may not match expected approval behavior.',
        'This matters because human review helps prevent loss.',
        'Approve or reject after reviewing the details.',
      ],
      executive: [
        'Shows possible payment fraud requiring business oversight.',
        'It reflects direct financial exposure to the bank.',
        'No action unless the case is escalated for decision.',
      ],
    },
    'threat trend': {
      analyst: [
        'Shows whether security risk is rising or easing over time.',
        'This helps you judge investigation urgency.',
        'No action unless the trend is climbing.',
      ],
      manager: [
        'Shows whether overall security risk is increasing or decreasing.',
        'This matters because rising trends may need faster decisions.',
        'Review only if the trend continues upward.',
      ],
      executive: [
        'Shows the direction of the bank’s overall security exposure.',
        'It helps leadership understand current security posture.',
        'No action needed unless the trend rises.',
      ],
    },
    'active threats': {
      analyst: [
        'Shows serious threats that still need active handling.',
        'This helps you focus on the most urgent work.',
        'Review the queue and move quickly on priority cases.',
      ],
      manager: [
        'Shows how many active threats need attention now.',
        'This matters because unresolved threats can raise bank risk.',
        'Review only if the number keeps growing.',
      ],
      executive: [
        'Shows the number of active threats across the bank.',
        'It reflects current pressure on security operations.',
        'No action unless the count continues to increase.',
      ],
    },
    'risk index': {
      analyst: [
        'Shows the overall level of current security risk.',
        'This helps you judge investigation urgency across the queue.',
        'Use it to guide priorities, not as a final decision.',
      ],
      manager: [
        'Shows the bank’s current overall risk level.',
        'This matters because it supports faster risk decisions.',
        'Review when the score moves sharply upward.',
      ],
      executive: [
        'Shows a simple view of overall bank security exposure.',
        'It helps leadership track the current security posture.',
        'No action unless the score rises materially.',
      ],
    },
  };

  const key = String(label || '').trim().toLowerCase();
  return copy[key]?.[view] || null;
}

export default function MetricCard({ label, value, delta, tone = 'default', helper, role = 'employee' }) {
  const tooltip = getMetricTooltip(label, role);

  return (
    <div className="group relative soc-panel-muted min-h-[136px]" tabIndex={tooltip ? 0 : undefined}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">{label}</p>
        <StatusBadge tone={tone}>{delta}</StatusBadge>
      </div>
      <p className="mt-4 font-headline text-[40px] font-extrabold tracking-tight text-white">{value}</p>
      {helper ? <p className="mt-2 text-xs soc-text-muted">{helper}</p> : null}
      {tooltip ? (
        <div className="pointer-events-none absolute left-4 right-4 top-full z-20 mt-2 rounded-2xl border border-[rgba(96,126,180,0.42)] bg-[rgba(12,18,28,0.96)] p-3 text-sm text-[#d8e2ff] opacity-0 shadow-[0_18px_40px_rgba(0,0,0,0.35)] transition duration-150 group-hover:opacity-100 group-focus-within:opacity-100">
          {tooltip.map((line) => (
            <p key={line} className="leading-5">
              {line}
            </p>
          ))}
        </div>
      ) : null}
    </div>
  );
}

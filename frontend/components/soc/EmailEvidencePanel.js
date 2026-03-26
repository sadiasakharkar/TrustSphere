import StatusBadge from './StatusBadge';

function DetailRow({ label, value }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-[rgba(65,71,85,0.3)] py-3 last:border-b-0 last:pb-0">
      <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">{label}</p>
      <p className="max-w-[70%] text-right text-sm leading-6 text-white">{value || 'Unavailable'}</p>
    </div>
  );
}

export default function EmailEvidencePanel({ email }) {
  if (!email) return null;

  return (
    <div className="pb-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="soc-kicker">Email Evidence</p>
          <h2 className="mt-2 text-base font-semibold text-white">{email.subject}</h2>
          <p className="mt-2 text-sm leading-6 soc-text-muted">{email.aiSummary}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge tone={email.severity}>{email.severity}</StatusBadge>
          <StatusBadge tone="medium">Score {email.phishingScore}</StatusBadge>
          <StatusBadge tone="medium">Confidence {email.confidence}</StatusBadge>
        </div>
      </div>

      <div className="mt-5 grid gap-6 lg:grid-cols-[0.95fr,1.05fr]">
        <div className="soc-panel-muted">
          <DetailRow label="From" value={email.from} />
          <DetailRow label="To" value={email.to} />
          <DetailRow label="Reply-To" value={email.replyTo} />
          <DetailRow label="Received" value={email.timestamp} />
          <DetailRow label="Verdict" value={email.verdict} />
        </div>

        <div className="space-y-4">
          <div className="soc-panel-muted">
            <p className="text-sm font-semibold text-white">Body snippet</p>
            <p className="mt-2 text-sm leading-6 soc-text-muted">{email.bodySnippet}</p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="soc-panel-muted">
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">SPF</p>
              <p className="mt-2 text-sm font-semibold text-white">{email.spf}</p>
            </div>
            <div className="soc-panel-muted">
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">DKIM</p>
              <p className="mt-2 text-sm font-semibold text-white">{email.dkim}</p>
            </div>
            <div className="soc-panel-muted">
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">DMARC</p>
              <p className="mt-2 text-sm font-semibold text-white">{email.dmarc}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <div className="soc-panel-muted">
          <p className="text-sm font-semibold text-white">Suspicious indicators</p>
          <div className="mt-3 space-y-2">
            {(email.indicators || []).map((item) => (
              <p key={item} className="text-sm leading-6 soc-text-muted">{item}</p>
            ))}
          </div>
        </div>

        <div className="soc-panel-muted">
          <p className="text-sm font-semibold text-white">Extracted URLs</p>
          <div className="mt-3 space-y-2">
            {(email.urls || []).map((item) => (
              <p key={item} className="break-all text-sm leading-6 soc-text-muted">{item}</p>
            ))}
          </div>
        </div>

        <div className="soc-panel-muted">
          <p className="text-sm font-semibold text-white">Attachments</p>
          <div className="mt-3 space-y-2">
            {(email.attachments || []).map((item) => (
              <p key={item} className="text-sm leading-6 soc-text-muted">{item}</p>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 soc-panel-muted">
        <p className="text-sm font-semibold text-white">Recommended actions</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {(email.actions || []).map((item) => (
            <span key={item} className="soc-badge border border-[rgba(65,71,85,0.55)] bg-[rgba(16,20,26,0.86)] text-[rgba(223,226,235,0.82)]">
              {item}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

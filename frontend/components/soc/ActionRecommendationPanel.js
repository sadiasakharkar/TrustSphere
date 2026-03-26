import StatusBadge from './StatusBadge';

function ScoreBar({ label, value, tone = '#adc6ff' }) {
  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-medium text-[rgba(223,226,235,0.82)]">{label}</p>
        <p className="text-xs soc-text-muted">{value}</p>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-[rgba(65,71,85,0.42)]">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${value}%`, background: tone }} />
      </div>
    </div>
  );
}

export default function ActionRecommendationPanel({
  plan,
  executingActionId = '',
  executionMessage = '',
  actionDisabled = false,
  actionDisabledReason = '',
  onExecuteAction,
  onExecutePlaybook
}) {
  const recommended = plan?.recommendedAction;
  const alternatives = plan?.alternatives || [];
  const comparison = plan?.comparison || [];
  const playbook = plan?.recommendedPlaybook;

  if (!recommended) return null;

  return (
    <section className="soc-panel">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-3xl">
          <p className="soc-kicker">AI Recommended Response</p>
          <h2 className="soc-section-title mt-2">Most appropriate action right now</h2>
          <p className="mt-2 text-sm leading-6 soc-text-muted">
            {plan.reasoningSummary}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge tone="ready">{recommended.score} suitability</StatusBadge>
          <StatusBadge tone="medium">{recommended.confidence}% confidence</StatusBadge>
          <StatusBadge tone={recommended.status}>{recommended.status}</StatusBadge>
        </div>
      </div>

      <div className="mt-5 grid gap-6 xl:grid-cols-[1.08fr,0.92fr]">
        <div className="soc-recommendation-panel rounded-2xl border p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#4ae176]">Best next move</p>
              <h3 className="mt-2 text-xl font-semibold text-white">{recommended.label}</h3>
              <p className="mt-3 text-sm leading-6 soc-text-muted">{recommended.detail}</p>
            </div>
            <div className="rounded-full border border-[rgba(74,225,118,0.18)] bg-[rgba(74,225,118,0.08)] px-3 py-1.5 text-xs font-bold uppercase tracking-[0.14em] text-[#4ae176]">
              Ranked #1
            </div>
          </div>

          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            <ScoreBar label="Containment effectiveness" value={recommended.effectiveness} tone="#4ae176" />
            <ScoreBar label="Urgency match" value={recommended.urgency} tone="#ffb3ad" />
            <ScoreBar label="Confidence" value={recommended.confidence} tone="#adc6ff" />
            <ScoreBar label="Reversibility" value={recommended.reversibility} tone="#f5d36c" />
          </div>

          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            <div className="soc-panel-muted">
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#adc6ff]">Why this is best</p>
              <p className="mt-2 text-sm leading-6 soc-text-muted">{recommended.rationale}</p>
            </div>
            <div className="soc-panel-muted">
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#ffb3ad]">Tradeoff</p>
              <p className="mt-2 text-sm leading-6 soc-text-muted">{recommended.tradeoff}</p>
            </div>
          </div>

          <div className="mt-5 flex flex-wrap gap-3">
            <button
              type="button"
              className="soc-btn-primary"
              onClick={() => onExecuteAction?.(recommended)}
              disabled={actionDisabled || executingActionId === recommended.id}
              title={actionDisabled ? actionDisabledReason : ''}
            >
              {actionDisabled ? 'Live sync required' : executingActionId === recommended.id ? 'Executing...' : 'Execute recommended action'}
            </button>
            {playbook ? (
              <button
                type="button"
                className="soc-btn-secondary"
                onClick={() => onExecutePlaybook?.(playbook)}
                disabled={actionDisabled || executingActionId === playbook.id}
                title={actionDisabled ? actionDisabledReason : ''}
              >
                {actionDisabled ? 'Live sync required' : `Run ${playbook.name}`}
              </button>
            ) : null}
          </div>
          {executionMessage ? <p className="mt-3 text-sm text-[#adc6ff]">{executionMessage}</p> : null}
          {actionDisabled && actionDisabledReason ? <p className="mt-3 text-sm text-[#ffb3ad]">{actionDisabledReason}</p> : null}
        </div>

        <div className="space-y-4">
          <div className="soc-panel-muted">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Alternative actions</p>
            <div className="mt-4 space-y-3">
              {alternatives.map((action) => (
                <div key={action.id} className="rounded-xl border border-[rgba(65,71,85,0.42)] bg-[rgba(16,20,26,0.56)] px-4 py-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-white">{action.label}</p>
                      <p className="mt-1 text-xs soc-text-muted">Suitability {action.score} - Disruption {action.disruption}%</p>
                    </div>
                    <button
                      type="button"
                      className="soc-btn-ghost"
                      onClick={() => onExecuteAction?.(action)}
                      disabled={actionDisabled || executingActionId === action.id}
                      title={actionDisabled ? actionDisabledReason : ''}
                    >
                      {actionDisabled ? 'Offline' : executingActionId === action.id ? 'Executing...' : 'Run'}
                    </button>
                  </div>
                  <p className="mt-2 text-sm leading-6 soc-text-muted">{action.whyNotBest}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="soc-panel-muted">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Decision matrix</p>
            <div className="mt-4 space-y-3">
              {comparison.map((action) => (
                <div key={`${action.id}-matrix`} className="grid gap-3 rounded-xl border border-[rgba(65,71,85,0.38)] bg-[rgba(16,20,26,0.48)] px-4 py-3 sm:grid-cols-[minmax(0,1fr)_72px_72px] sm:items-center">
                  <div>
                    <p className="text-sm font-semibold text-white">{action.label}</p>
                    <p className="mt-1 text-xs soc-text-muted">{action.detail}</p>
                  </div>
                  <div className="sm:text-right">
                    <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-[rgba(193,198,215,0.58)]">Score</p>
                    <p className="mt-1 text-sm font-semibold text-white">{action.score}</p>
                  </div>
                  <div className="sm:text-right">
                    <p className="text-[11px] font-bold uppercase tracking-[0.14em] text-[rgba(193,198,215,0.58)]">Impact</p>
                    <p className="mt-1 text-sm font-semibold text-white">{action.disruption}%</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

import SeverityBadge from './SeverityBadge';

export default function PlaybookChecklist({ steps = [] }) {
  return (
    <div className="space-y-3">
      {steps.map((step) => (
        <div key={step.title || step.step} className="soc-panel-muted">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-white">{step.title || step.step}</p>
              <p className="mt-1 text-sm leading-6 soc-text-muted">{step.detail || step.status}</p>
              {step.owner ? <p className="mt-2 text-xs text-[rgba(193,198,215,0.68)]">Owner: {step.owner}</p> : null}
            </div>
            {'confidence' in step ? <SeverityBadge level="medium">{step.confidence}% confidence</SeverityBadge> : null}
          </div>
        </div>
      ))}
    </div>
  );
}

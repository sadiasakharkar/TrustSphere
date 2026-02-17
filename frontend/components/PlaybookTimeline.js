export default function PlaybookTimeline({ steps }) {
  return (
    <div className="card p-4">
      <h3 className="mb-4 text-lg font-semibold text-white">Response Playbook</h3>
      <div className="space-y-3">
        {steps.map((step, idx) => (
          <div key={step.title} className="rounded-lg border border-white/10 bg-bg/50 p-3">
            <p className="text-sm font-semibold text-accent">Step {idx + 1}: {step.title}</p>
            <p className="mt-1 text-sm text-text/90">{step.detail}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

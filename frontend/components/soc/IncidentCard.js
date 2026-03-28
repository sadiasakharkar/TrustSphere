import { useMemo, useState } from 'react';
import Modal from '../Modal';
import { formatCountdown } from '../../data/hitlIncidents';
import StatusBadge from './StatusBadge';

const modifyOptions = ['Freeze Account', 'Block Transaction', 'Monitor Only'];

function formatAuditTime(timestamp) {
  return new Intl.DateTimeFormat('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date(timestamp));
}

export default function IncidentCard({
  incident,
  role = 'employee',
  currentTime = Date.now(),
  onApprove,
  onReject,
  onModify,
}) {
  const [modifyOpen, setModifyOpen] = useState(false);

  const riskTone = useMemo(() => {
    if (incident.riskScore >= 90) return 'critical';
    if (incident.riskScore >= 75) return 'high';
    if (incident.riskScore >= 60) return 'medium';
    return 'low';
  }, [incident.riskScore]);

  const canAct = role === 'analyst' && incident.status === 'PENDING_APPROVAL';
  const countdown = incident.status === 'PENDING_APPROVAL'
    ? formatCountdown(incident.approvalDeadline, currentTime)
    : incident.status.replaceAll('_', ' ');

  return (
    <>
      <section className="soc-panel">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge tone={riskTone}>{incident.riskType}</StatusBadge>
            <StatusBadge tone={incident.status}>{incident.status.replaceAll('_', ' ')}</StatusBadge>
          </div>
          <div className="text-right">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">Score</p>
            <p className="mt-1 text-2xl font-extrabold text-white">{incident.riskScore}</p>
          </div>
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-[1.1fr,0.9fr]">
          <div className="space-y-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">User</p>
              <p className="mt-2 text-lg font-semibold text-white">{incident.user}</p>
            </div>

            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">Timeline</p>
              <ul className="mt-2 space-y-2">
                {incident.timeline.map((item) => (
                  <li key={item} className="rounded-xl border border-[rgba(65,71,85,0.45)] bg-[rgba(24,28,34,0.85)] px-3 py-2 text-sm text-white">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="space-y-4">
            <div className="soc-panel-muted">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">AI Action</p>
              <p className="mt-2 text-base font-semibold text-white">{incident.aiSuggestion}</p>
            </div>

            <div className="soc-panel-muted">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">Confidence</p>
              <p className="mt-2 text-2xl font-extrabold text-white">{incident.confidence}%</p>
            </div>

            <div className="soc-panel-muted">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">Timer</p>
              <p className="mt-2 text-base font-semibold text-white">
                {incident.status === 'PENDING_APPROVAL' ? `Auto action in ${countdown}` : countdown}
              </p>
            </div>
          </div>
        </div>

        <div className="mt-5">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">Audit</p>
          <div className="mt-3 grid gap-2">
            {(incident.auditTrail || []).map((entry) => (
              <div key={entry.id} className="flex items-center justify-between rounded-xl border border-[rgba(65,71,85,0.45)] bg-[rgba(24,28,34,0.85)] px-3 py-2 text-sm">
                <span className="font-medium text-white">{entry.label}</span>
                <span className="soc-text-muted">{formatAuditTime(entry.timestamp)}</span>
              </div>
            ))}
          </div>
        </div>

        {role === 'analyst' ? (
          <div className="mt-5 flex flex-wrap gap-3">
            <button className="soc-btn-primary" disabled={!canAct} onClick={() => onApprove?.(incident.id)}>
              Approve
            </button>
            <button className="soc-btn-secondary" disabled={!canAct} onClick={() => setModifyOpen(true)}>
              Modify
            </button>
            <button className="soc-btn-ghost" disabled={!canAct} onClick={() => onReject?.(incident.id)}>
              Reject
            </button>
          </div>
        ) : null}
      </section>

      <Modal title="Modify Action" open={modifyOpen} onClose={() => setModifyOpen(false)}>
        <div className="grid gap-3">
          {modifyOptions.map((option) => (
            <button
              key={option}
              type="button"
              className="soc-btn-secondary w-full justify-start"
              onClick={() => {
                onModify?.(incident.id, option);
                setModifyOpen(false);
              }}
            >
              {option}
            </button>
          ))}
        </div>
      </Modal>
    </>
  );
}

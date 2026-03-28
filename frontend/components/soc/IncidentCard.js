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

function buildConsoleOutput(command, incident) {
  const normalized = String(command || '').trim();
  if (!normalized) return [];
  if (normalized === 'help') {
    return ['help', `incident ${incident.id}`, 'logs', 'timeline', 'risk-analysis'];
  }
  if (normalized.startsWith('incident')) {
    return [
      `id ${incident.id}`,
      `user ${incident.user}`,
      `status ${incident.status}`,
      `responder ${incident.assignedResponder || 'unassigned'}`,
    ];
  }
  if (normalized === 'logs') {
    return (incident.activityLog || []).map((entry) => `${entry.action} ${entry.user}`);
  }
  if (normalized === 'timeline') {
    return (incident.timeline || []).map((entry) => entry);
  }
  if (normalized === 'risk-analysis') {
    return [
      `score ${incident.riskScore}`,
      `type ${incident.riskType}`,
      `confidence ${incident.confidence}%`,
      `action ${incident.aiSuggestion}`,
    ];
  }
  return ['unknown command'];
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
  const [consoleOpen, setConsoleOpen] = useState(false);
  const [activityOpen, setActivityOpen] = useState(false);
  const [consoleInput, setConsoleInput] = useState('help');
  const [consoleLines, setConsoleLines] = useState(() => buildConsoleOutput('help', incident));

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
              <div className="mt-3 space-y-1 text-sm">
                <p className="text-white">Responder: <span className="soc-text-muted">{incident.assignedResponder || 'Unassigned'}</span></p>
                <p className="text-white">Approved: <span className="soc-text-muted">{incident.approvedBy || 'Pending'}</span></p>
              </div>
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

            <div className="soc-panel-muted">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">Network</p>
              <div className="mt-2 space-y-1 text-sm text-white">
                <p>SRC IP: <span className="soc-text-muted">{incident.networkInfo?.srcIp || 'n/a'}</span></p>
                <p>DST: <span className="soc-text-muted">{incident.networkInfo?.dstService || 'n/a'}</span></p>
                <p>Proto: <span className="soc-text-muted">{incident.networkInfo?.protocol || 'n/a'}</span></p>
                <p>Anom: <span className="soc-text-muted">{incident.networkInfo?.anomaly || 'n/a'}</span></p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-5">
          <button
            type="button"
            className="soc-btn-ghost px-0 text-sm"
            onClick={() => setActivityOpen((value) => !value)}
          >
            {activityOpen ? 'Hide Log' : 'Show Log'}
          </button>
          {activityOpen ? (
            <div className="mt-3 grid gap-2">
              {(incident.activityLog || []).map((entry, index) => (
                <div key={`${entry.timestamp}-${index}`} className="flex items-center justify-between rounded-xl border border-[rgba(65,71,85,0.45)] bg-[rgba(24,28,34,0.85)] px-3 py-2 text-sm">
                  <span className="font-medium text-white">{entry.action}</span>
                  <span className="soc-text-muted">{formatAuditTime(entry.timestamp)}</span>
                </div>
              ))}
              {(incident.auditTrail || []).map((entry) => (
                <div key={entry.id} className="flex items-center justify-between rounded-xl border border-[rgba(65,71,85,0.45)] bg-[rgba(24,28,34,0.85)] px-3 py-2 text-sm">
                  <span className="font-medium text-white">{entry.label}</span>
                  <span className="soc-text-muted">{formatAuditTime(entry.timestamp)}</span>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <button className="soc-btn-secondary" type="button" onClick={() => setConsoleOpen(true)}>
            Open Console
          </button>
          {role === 'analyst' ? (
            <>
            <button className="soc-btn-primary" disabled={!canAct} onClick={() => onApprove?.(incident.id)}>
              Approve
            </button>
            <button className="soc-btn-secondary" disabled={!canAct} onClick={() => setModifyOpen(true)}>
              Modify
            </button>
            <button className="soc-btn-ghost" disabled={!canAct} onClick={() => onReject?.(incident.id)}>
              Reject
            </button>
            </>
          ) : null}
        </div>
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

      <Modal title="Console" open={consoleOpen} onClose={() => setConsoleOpen(false)}>
        <div className="space-y-3 rounded-xl border border-[rgba(65,71,85,0.45)] bg-[rgba(10,14,20,0.92)] p-4 font-mono text-sm text-[#d8e2ff]">
          <div className="space-y-1">
            {consoleLines.map((line, index) => (
              <div key={`${line}-${index}`}>{line}</div>
            ))}
          </div>
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              setConsoleLines(buildConsoleOutput(consoleInput, incident));
            }}
          >
            <input
              className="soc-input font-mono"
              value={consoleInput}
              onChange={(event) => setConsoleInput(event.target.value)}
              placeholder="help"
            />
            <button type="submit" className="soc-btn-secondary">Run</button>
          </form>
        </div>
      </Modal>
    </>
  );
}

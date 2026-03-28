const APPROVAL_WINDOW_MS = 60 * 1000;

function buildDeadline(offsetSeconds = 60) {
  return new Date(Date.now() + offsetSeconds * 1000).toISOString();
}

function buildAudit(timestamp, label, actor = 'AI') {
  return {
    id: `${label}-${timestamp}`,
    label,
    actor,
    timestamp,
  };
}

export function createSeedIncidents() {
  const now = Date.now();
  return [
    {
      id: 'HITL-1001',
      user: 'maya.patel',
      assignedResponder: 'R. Singh',
      riskScore: 96,
      riskType: 'Credential Abuse',
      timeline: ['Login burst', 'Geo mismatch', 'Token reuse'],
      aiSuggestion: 'Freeze Account',
      confidence: 94,
      status: 'PENDING_APPROVAL',
      approvalDeadline: buildDeadline(60),
      approvedBy: null,
      networkInfo: {
        host: 'payments-app-01',
        ip: '203.0.113.41',
      },
      auditTrail: [
        buildAudit(new Date(now - 15000).toISOString(), 'AI Suggested', 'AI'),
      ],
    },
    {
      id: 'HITL-1002',
      user: 'svc.payments',
      assignedResponder: 'M. Khan',
      riskScore: 89,
      riskType: 'Privilege Spike',
      timeline: ['Role change', 'Host pivot', 'Vault access'],
      aiSuggestion: 'Block Transaction',
      confidence: 91,
      status: 'PENDING_APPROVAL',
      approvalDeadline: buildDeadline(42),
      approvedBy: null,
      networkInfo: {
        host: 'vault-gateway-02',
        ip: '10.22.4.18',
      },
      auditTrail: [
        buildAudit(new Date(now - 24000).toISOString(), 'AI Suggested', 'AI'),
      ],
    },
  ];
}

export function formatCountdown(deadline, currentTime) {
  const remainingMs = Math.max(new Date(deadline).getTime() - currentTime, 0);
  const totalSeconds = Math.ceil(remainingMs / 1000);
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
  const seconds = String(totalSeconds % 60).padStart(2, '0');
  return `${minutes}:${seconds}`;
}

export function withAuditEntry(incident, label, actor) {
  return {
    ...incident,
    auditTrail: [
      ...(incident.auditTrail || []),
      buildAudit(new Date().toISOString(), label, actor),
    ],
  };
}

export { APPROVAL_WINDOW_MS };

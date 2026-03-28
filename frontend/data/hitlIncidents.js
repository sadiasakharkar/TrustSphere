const APPROVAL_WINDOW_MS = 60 * 1000;

const responderByRiskType = {
  'Credential Abuse': { name: 'R. Singh', email: 'r.singh@trustsphere.local' },
  'Privilege Spike': { name: 'M. Khan', email: 'm.khan@trustsphere.local' },
  default: { name: 'A. Cole', email: 'a.cole@trustsphere.local' },
};

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

function buildActivity(action, user, timestamp) {
  return {
    action,
    user,
    timestamp,
  };
}

export function resolveResponder(riskType) {
  return responderByRiskType[riskType] || responderByRiskType.default;
}

export function sendIncidentEmail(responderEmail, incident) {
  return {
    to: responderEmail,
    subject: `Incident ${incident.id}`,
    sentAt: new Date().toISOString(),
    status: 'SENT',
  };
}

function createIncident(seed, createdAt) {
  const responder = resolveResponder(seed.riskType);
  const emailNotice = sendIncidentEmail(responder.email, seed);
  return {
    ...seed,
    assignedResponder: responder.name,
    responderEmail: responder.email,
    activityLog: [
      buildActivity('AI Suggested', 'AI', new Date(createdAt - 15000).toISOString()),
      buildActivity('Assigned', responder.name, new Date(createdAt - 12000).toISOString()),
      buildActivity('Email Sent', responder.email, emailNotice.sentAt),
    ],
  };
}

export function createSeedIncidents() {
  const now = Date.now();
  return [
    createIncident({
      id: 'HITL-1001',
      user: 'maya.patel',
      riskScore: 96,
      riskType: 'Credential Abuse',
      timeline: ['Login burst', 'Geo mismatch', 'Token reuse'],
      aiSuggestion: 'Freeze Account',
      confidence: 94,
      status: 'PENDING_APPROVAL',
      approvalDeadline: buildDeadline(60),
      approvedBy: null,
      networkInfo: {
        srcIp: '203.0.113.41',
        dstService: 'payments-api',
        protocol: 'TLS',
        anomaly: 'Burst Auth',
      },
      auditTrail: [
        buildAudit(new Date(now - 15000).toISOString(), 'AI Suggested', 'AI'),
        buildAudit(new Date(now - 12000).toISOString(), 'Assigned', 'R. Singh'),
      ],
    }, now),
    createIncident({
      id: 'HITL-1002',
      user: 'svc.payments',
      riskScore: 89,
      riskType: 'Privilege Spike',
      timeline: ['Role change', 'Host pivot', 'Vault access'],
      aiSuggestion: 'Block Transaction',
      confidence: 91,
      status: 'PENDING_APPROVAL',
      approvalDeadline: buildDeadline(42),
      approvedBy: null,
      networkInfo: {
        srcIp: '10.22.4.18',
        dstService: 'vault-gateway',
        protocol: 'TCP',
        anomaly: 'Role Pivot',
      },
      auditTrail: [
        buildAudit(new Date(now - 24000).toISOString(), 'AI Suggested', 'AI'),
        buildAudit(new Date(now - 21000).toISOString(), 'Assigned', 'M. Khan'),
      ],
    }, now),
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

export function withActivityEntry(incident, action, user) {
  return {
    ...incident,
    activityLog: [
      ...(incident.activityLog || []),
      buildActivity(action, user, new Date().toISOString()),
    ],
  };
}

export { APPROVAL_WINDOW_MS };

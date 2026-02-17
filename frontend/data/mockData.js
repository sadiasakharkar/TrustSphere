export const analystMetrics = [
  { label: 'Total Alerts Today', value: 482, delta: '+12.8%', tone: 'info', helper: '24h rolling' },
  { label: 'Critical Alerts', value: 37, delta: '+4.2%', tone: 'critical', helper: 'Needs triage' },
  { label: 'Open Incidents', value: 19, delta: '+2.0%', tone: 'high', helper: 'Queue depth' },
  { label: 'MTTD', value: '11m 24s', delta: '-9.1%', tone: 'success', helper: 'Faster detection' }
];

export const adminMetrics = [
  ...analystMetrics,
  { label: 'Active Users', value: 56, delta: '+3.7%', tone: 'info', helper: 'SOC + Risk teams' },
  { label: 'System Health', value: '99.97%', delta: '+0.4%', tone: 'success', helper: 'Air-gapped cluster' },
  { label: 'Pending Model Training', value: 2, delta: '+1', tone: 'violet', helper: 'Scheduled tonight' }
];

export const aiPipeline = [
  { module: 'Data Ingestion', status: 'Operational', detail: 'SIEM, EDR, IAM, Core Banking logs streaming locally' },
  { module: 'Normalization', status: 'Operational', detail: 'Schema harmonization and timestamp alignment complete' },
  { module: 'Feature Extraction', status: 'Operational', detail: 'Entity behavior vectors generated every 5 minutes' },
  { module: 'Anomaly Detection', status: 'High Activity', detail: 'Behavior drift scores above threshold in 4 segments' },
  { module: 'Correlation Engine', status: 'Operational', detail: 'Cross-source incident stitching active' },
  { module: 'Attack Graph Builder', status: 'Operational', detail: 'Path fidelity scoring at 0.93 confidence' },
  { module: 'Playbook Generation', status: 'Operational', detail: 'Auto-response actions generated with safety guardrails' },
  { module: 'Narrative Intelligence', status: 'Operational', detail: 'MITRE-mapped summaries produced for analyst briefings' }
];

export const anomalyTrend = [22, 19, 27, 31, 28, 35, 40, 34, 42, 49, 46, 52];
export const severityDistribution = [14, 26, 34, 18, 8];
export const behavioralDeviationByZone = [8, 11, 14, 17, 13, 19];
export const correlatedAlertsByZone = [6, 9, 12, 14, 11, 16];

export const alertTypeSplit = [
  { name: 'Phishing', value: 34 },
  { name: 'Anomalous Login', value: 24 },
  { name: 'Malware', value: 16 },
  { name: 'Privilege Escalation', value: 14 },
  { name: 'Data Exfiltration', value: 12 }
];

export const incidents = [
  {
    id: 'INC-21403',
    timestamp: '2026-02-17 10:23:11',
    entity: 'acct-payroll-09',
    eventType: 'Privilege Escalation',
    riskScore: 92,
    status: 'Investigating',
    severity: 'Critical',
    affected: '3 hosts, 2 users'
  },
  {
    id: 'INC-21404',
    timestamp: '2026-02-17 10:41:58',
    entity: 'teller-branch-11',
    eventType: 'Anomalous Login',
    riskScore: 78,
    status: 'Open',
    severity: 'High',
    affected: '1 host, 1 user'
  },
  {
    id: 'INC-21405',
    timestamp: '2026-02-17 11:02:42',
    entity: 'loan-underwrite-03',
    eventType: 'Malware Signature',
    riskScore: 71,
    status: 'Contained',
    severity: 'High',
    affected: '2 hosts'
  },
  {
    id: 'INC-21406',
    timestamp: '2026-02-17 11:27:06',
    entity: 'atm-cluster-02',
    eventType: 'Data Exfiltration',
    riskScore: 88,
    status: 'Escalated',
    severity: 'Critical',
    affected: '4 hosts, 1 service account'
  },
  {
    id: 'INC-21407',
    timestamp: '2026-02-17 12:05:17',
    entity: 'compliance-reports-01',
    eventType: 'Phishing',
    riskScore: 56,
    status: 'Open',
    severity: 'Medium',
    affected: '1 user'
  }
];

export const analyticsTrend = [9, 11, 13, 10, 17, 21, 18, 23, 20, 26, 24, 29];

export const anomalousEntities = [
  { entity: 'acct-payroll-09', type: 'Host', score: 96, events: 42, signal: 'Lateral movement burst' },
  { entity: 'jane.carter', type: 'User', score: 91, events: 33, signal: 'Impossible travel + token refresh' },
  { entity: 'teller-branch-11', type: 'Host', score: 86, events: 29, signal: 'Off-hour privileged command chain' },
  { entity: 'svc-wire-transfer', type: 'User', score: 81, events: 24, signal: 'API call volume anomaly' },
  { entity: 'atm-cluster-02', type: 'Host', score: 77, events: 18, signal: 'Outbound transfer spike' }
];

export const users = [
  { id: 'U-001', name: 'Avery Collins', role: 'Analyst', status: 'Active' },
  { id: 'U-002', name: 'Maya Patel', role: 'Admin', status: 'Active' },
  { id: 'U-003', name: 'Jordan Lee', role: 'Analyst', status: 'Suspended' },
  { id: 'U-004', name: 'Riley Grant', role: 'Analyst', status: 'Active' },
  { id: 'U-005', name: 'Noah Reyes', role: 'Analyst', status: 'Active' }
];

export const modelTrainingStatus = [
  { model: 'Behavioral Baseline v5.3', state: 'Running', eta: '01h 12m', lastRun: '2026-02-16 23:05' },
  { model: 'Incident Correlator v2.8', state: 'Queued', eta: '03h 40m', lastRun: '2026-02-16 22:10' },
  { model: 'Narrative Generator v1.9', state: 'Healthy', eta: 'N/A', lastRun: '2026-02-17 09:00' }
];

export const auditLogs = [
  { id: 'AUD-901', timestamp: '2026-02-17 12:14:50', actor: 'Maya Patel', action: 'Changed alert source config', result: 'Success' },
  { id: 'AUD-902', timestamp: '2026-02-17 12:10:17', actor: 'TrustSphere AI', action: 'Generated playbook for INC-21403', result: 'Success' },
  { id: 'AUD-903', timestamp: '2026-02-17 11:55:41', actor: 'Avery Collins', action: 'Escalated INC-21406', result: 'Success' }
];

export const playbookSteps = [
  {
    title: 'Containment',
    detail: 'Isolate impacted hosts, disable compromised credentials, and block outbound C2 channels.',
    owner: 'SOC Tier-1',
    confidence: 96
  },
  {
    title: 'Investigation',
    detail: 'Correlate SIEM, EDR, and IAM events against MITRE ATT&CK T1566, T1078, T1021.',
    owner: 'Threat Hunt Team',
    confidence: 93
  },
  {
    title: 'Eradication',
    detail: 'Remove persistence artifacts and revoke suspicious privilege grants from domain controllers.',
    owner: 'IR Engineering',
    confidence: 91
  },
  {
    title: 'Recovery',
    detail: 'Restore critical services, validate controls, and monitor risk regression for 24 hours.',
    owner: 'Platform Ops',
    confidence: 89
  },
  {
    title: 'Escalation',
    detail: 'Notify CISO, Risk Office, and legal compliance desk with fidelity score and impact matrix.',
    owner: 'SOC Lead',
    confidence: 94
  }
];

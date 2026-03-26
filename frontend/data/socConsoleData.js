import { aiPipeline, alertTypeSplit, anomalousEntities, auditLogs, incidents, modelTrainingStatus, playbookSteps, users } from './mockData';

export const overviewSnapshot = {
  headline: {
    title: 'Enterprise SOC Overview',
    subtitle: 'Unified intelligence across UEBA, graph analytics, fraud detectors, and local SOC reasoning.',
    status: 'Air-gapped production simulation',
    updatedAt: '2026-03-24T18:42:00Z'
  },
  metrics: [
    { label: 'Active Incidents', value: 19, delta: '+3', status: 'critical', helper: '4 require containment approval' },
    { label: 'High-Risk Entities', value: 42, delta: '+8%', status: 'high', helper: 'Users, hosts, and service accounts' },
    { label: 'Model Health', value: '99.2%', delta: 'Stable', status: 'healthy', helper: 'Inference and queue latency within SLA' },
    { label: 'Analyst SLA', value: '13m', delta: '-2m', status: 'healthy', helper: 'Median time to first triage action' }
  ],
  criticalQueue: incidents.slice(0, 4),
  modelHealth: [
    { name: 'UEBA Anomaly Model', status: 'Healthy', detail: 'Isolation Forest inference stable. Drift estimate 0.07.' },
    { name: 'Attack Graph Engine', status: 'High Activity', detail: '3 critical chains reconstructed in last 30 minutes.' },
    { name: 'SOC LLM Analyst', status: 'Ready', detail: 'Ollama local endpoint verified. Deterministic mode active.' },
    { name: 'Fraud Detector Suite', status: 'Healthy', detail: 'Email, URL, credential, attachment, and prompt guard online.' }
  ],
  pipeline: aiPipeline,
  notifications: [
    { id: 'NTF-1', title: 'Privileged session spike detected', detail: 'Admin activity on payroll segment doubled in 12 minutes.', severity: 'high', time: '2m ago' },
    { id: 'NTF-2', title: 'Prompt guard blocked analyst query', detail: 'Role override pattern prevented from reaching local LLM.', severity: 'medium', time: '8m ago' },
    { id: 'NTF-3', title: 'Threat graph severity increased', detail: 'Chain AG-204 reclassified from HIGH to CRITICAL.', severity: 'critical', time: '11m ago' }
  ]
};

export const monitoringFeed = Array.from({ length: 8 }).map((_, index) => ({
  id: `EVT-${3100 + index}`,
  timestamp: `2026-03-24 18:${String(10 + index).padStart(2, '0')}:12`,
  entity: ['svc-wire-transfer', 'branch-atm-02', 'alex.chen', 'loan-core-03'][index % 4],
  source: ['UEBA', 'Email AI', 'URL AI', 'Prompt Guard'][index % 4],
  eventType: ['after_hours_login', 'mass_file_access', 'geo_anomaly', 'policy_override_attempt'][index % 4],
  severity: ['Critical', 'High', 'Medium', 'High'][index % 4],
  score: [92, 86, 71, 77][index % 4]
}));

export const triageSummary = {
  queue: incidents.map((incident, index) => ({
    ...incident,
    owner: ['Avery Collins', 'Unassigned', 'Riley Grant', 'Maya Patel', 'Unassigned'][index % 5],
    sla: ['12m', '21m', 'Resolved', '8m', '36m'][index % 5],
    tactic: ['Credential Access', 'Initial Access', 'Execution', 'Exfiltration', 'Delivery'][index % 5]
  }))
};

export const incidentWorkspace = {
  summary: {
    id: 'INC-21403',
    title: 'Suspicious privilege escalation with cross-segment lateral movement',
    severity: 'Critical',
    confidence: '0.94',
    status: 'Investigating',
    owner: 'Avery Collins',
    users: ['jane.carter', 'svc-payroll-admin'],
    hosts: ['acct-payroll-09', 'dc-east-02'],
    mitre: ['TA0001 Initial Access', 'TA0004 Privilege Escalation', 'TA0008 Lateral Movement']
  },
  timeline: [
    { time: '02:14', title: 'Impossible-travel login detected', detail: 'User jane.carter authenticated from a new geography.' },
    { time: '02:19', title: 'Privileged token requested', detail: 'Service account elevation observed outside baseline.' },
    { time: '02:27', title: 'Lateral movement to domain controller', detail: 'Remote admin execution created on dc-east-02.' },
    { time: '02:41', title: 'High-volume outbound transfer', detail: 'Encrypted exfiltration path established to external IP.' }
  ],
  evidence: [
    { title: 'Behavioral deviation', content: 'After-hours activity ratio increased 4.6x above baseline for jane.carter.' },
    { title: 'Credential risk', content: 'Failed login burst followed by success from new device fingerprint.' },
    { title: 'Graph correlation', content: 'Attack chain intersects payroll segment and privileged admin assets.' }
  ],
  emailEvidence: {
    subject: 'Action required: payroll verification before 10:00 UTC',
    from: 'Payroll Security <payroll-security@secure-payroll-alerts.com>',
    to: 'jane.carter@trustsphere.local',
    replyTo: 'hr-processing@external-review.net',
    timestamp: '2026-03-24 02:11:43 UTC',
    verdict: 'Likely phishing',
    phishingScore: 94,
    severity: 'High',
    confidence: '0.96',
    spf: 'Fail',
    dkim: 'Fail',
    dmarc: 'Fail',
    bodySnippet: 'We detected a mismatch in your payroll profile. Re-validate your credentials immediately to avoid delayed salary processing.',
    indicators: [
      'Reply-To domain differs from sender domain.',
      'Urgent credential request tied to payroll disruption.',
      'Sender domain is newly observed in the environment.'
    ],
    urls: [
      'hxxps://secure-payroll-alerts.com/verify',
      'hxxps://bit.ly/3-payroll-check'
    ],
    attachments: [
      'Payroll_Adjustment_Form.zip'
    ],
    aiSummary: 'Authentication checks failed and the message uses payroll urgency plus credential collection language consistent with phishing.',
    actions: [
      'Quarantine email',
      'Block sender domain',
      'Notify recipient',
      'Search for similar messages'
    ]
  }
};

export const investigationWorkspace = {
  entities: anomalousEntities,
  relatedEvidence: [
    { id: 'IOC-201', type: 'Host', value: 'acct-payroll-09', note: 'Repeated admin tool execution after token refresh.' },
    { id: 'IOC-202', type: 'IP', value: '185.193.12.44', note: 'Outbound session reused across two correlated chains.' },
    { id: 'IOC-203', type: 'User', value: 'jane.carter', note: 'Impossible-travel behavior paired with privilege anomaly.' }
  ]
};

export const graphWorkspace = {
  nodes: [
    { id: 'n1', label: 'jane.carter', type: 'user', risk: 'critical', x: 18, y: 45 },
    { id: 'n2', label: 'acct-payroll-09', type: 'host', risk: 'high', x: 36, y: 28 },
    { id: 'n3', label: 'dc-east-02', type: 'host', risk: 'critical', x: 56, y: 48 },
    { id: 'n4', label: '185.193.12.44', type: 'ip', risk: 'critical', x: 82, y: 35 }
  ],
  edges: [
    { from: 'n1', to: 'n2', label: 'credential_use' },
    { from: 'n2', to: 'n3', label: 'lateral_move' },
    { from: 'n3', to: 'n4', label: 'exfiltration' }
  ],
  chains: [
    { id: 'AG-204', title: 'Credential misuse to exfiltration chain', severity: 'Critical', confidence: '0.92' },
    { id: 'AG-198', title: 'Suspicious admin token pivot', severity: 'High', confidence: '0.81' }
  ]
};

export const responseWorkspace = {
  playbook: playbookSteps,
  approvals: [
    { step: 'Disable service account', status: 'Pending approval', owner: 'IR Lead' },
    { step: 'Block destination IP', status: 'Ready to execute', owner: 'Network Ops' },
    { step: 'Force credential rotation', status: 'In progress', owner: 'IAM Team' }
  ]
};

export const detectionsWorkspace = {
  detectors: [
    { name: 'Email Phishing', status: 'Healthy', version: 'v1.8.2', inferenceCount: '14,284', drift: 'Low', precision: '0.97' },
    { name: 'URL Classifier', status: 'Healthy', version: 'v2.1.0', inferenceCount: '48,121', drift: 'Low', precision: '0.98' },
    { name: 'Credential Exposure', status: 'High Activity', version: 'v1.4.7', inferenceCount: '3,212', drift: 'Moderate', precision: '0.93' },
    { name: 'Attachment Analysis', status: 'Healthy', version: 'v1.6.1', inferenceCount: '9,443', drift: 'Low', precision: '0.91' },
    { name: 'Prompt Injection Guard', status: 'Healthy', version: 'v1.2.5', inferenceCount: '1,145', drift: 'Low', precision: '0.99' }
  ]
};

export const reportsWorkspace = {
  reports: [
    { id: 'RPT-201', title: 'Executive summary: payroll lateral movement', severity: 'Critical', author: 'TrustSphere SOC Analyst', updated: '2026-03-24 18:31' },
    { id: 'RPT-202', title: 'Containment plan: external transfer suppression', severity: 'High', author: 'Avery Collins', updated: '2026-03-24 17:52' }
  ]
};

export const administrationWorkspace = {
  users,
  modelTrainingStatus,
  auditLogs,
  systemStatus: [
    { label: 'Inference Queue', value: 'Nominal' },
    { label: 'Redis Worker', value: 'Standby' },
    { label: 'Kafka Consumer', value: 'Connected' },
    { label: 'Ollama Health', value: 'Ready' }
  ]
};

export const notifications = overviewSnapshot.notifications;
export const detectorSplit = alertTypeSplit;

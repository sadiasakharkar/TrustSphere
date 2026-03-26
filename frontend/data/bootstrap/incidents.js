export const bootstrapIncidents = [
  {
    id: 'INC-RAN-401',
    title: 'Ransomware execution path detected on treasury workstation',
    severity: 'Critical',
    status: 'OPEN',
    assigned_to: 'Avery Collins',
    mitre_stage: 'TA0040 Impact',
    anomaly_score: 0.97,
    risk_score: 96,
    created_at: '2026-03-26 09:12:14',
    entities: ['mira.shah', 'treasury-ws-04', '185.199.44.12'],
    timeline: [
      { time: '09:12', title: 'Suspicious encryption behavior', detail: 'Endpoint telemetry detected rapid file rename and encryption sequence.' },
      { time: '09:15', title: 'Backup share access denied', detail: 'Ransomware process attempted to enumerate protected backup mounts.' },
      { time: '09:19', title: 'Containment initiated', detail: 'Host isolated from east-west traffic pending analyst approval.' }
    ],
    graph_nodes: [
      { id: 'inc-ran-u', label: 'mira.shah', type: 'user', risk: 'critical', x: 16, y: 32 },
      { id: 'inc-ran-h', label: 'treasury-ws-04', type: 'host', risk: 'critical', x: 42, y: 42 },
      { id: 'inc-ran-ip', label: '185.199.44.12', type: 'ip', risk: 'high', x: 76, y: 24 }
    ],
    graph_edges: [
      { from: 'inc-ran-u', to: 'inc-ran-h', label: 'login_from' },
      { from: 'inc-ran-h', to: 'inc-ran-ip', label: 'connected_to' }
    ],
    owner: 'Avery Collins',
    entity: 'treasury-ws-04',
    eventType: 'Ransomware Detected',
    affected: '1 host, 1 user',
    confidence: '0.97',
    users: ['mira.shah'],
    hosts: ['treasury-ws-04'],
    mitre: ['TA0040 Impact', 'TA0002 Execution'],
    evidence: [
      { title: 'Behavioral anomaly', content: 'File write volume increased 12.8x above workstation baseline in under three minutes.' },
      { title: 'Endpoint evidence', content: 'Unsigned process executed from user profile followed by mass encryption behavior.' },
      { title: 'Containment recommendation', content: 'Keep host isolated and validate adjacent SMB access before re-joining network.' }
    ]
  },
  {
    id: 'INC-CRD-402',
    title: 'Credential abuse against payroll admin identity',
    severity: 'Critical',
    status: 'INVESTIGATING',
    assigned_to: 'Riley Grant',
    mitre_stage: 'TA0006 Credential Access',
    anomaly_score: 0.94,
    risk_score: 91,
    created_at: '2026-03-26 09:24:48',
    entities: ['jane.carter', 'acct-payroll-09', '102.88.14.19'],
    timeline: [
      { time: '09:24', title: 'Impossible travel login', detail: 'Authentication originated from a new region 14 minutes after local office access.' },
      { time: '09:28', title: 'MFA fatigue burst', detail: 'Repeated push attempts ended in a single successful approval.' },
      { time: '09:31', title: 'Privileged session established', detail: 'Service token issued outside baseline payroll maintenance window.' }
    ],
    graph_nodes: [
      { id: 'inc-crd-u', label: 'jane.carter', type: 'user', risk: 'critical', x: 14, y: 45 },
      { id: 'inc-crd-h', label: 'acct-payroll-09', type: 'host', risk: 'high', x: 42, y: 36 },
      { id: 'inc-crd-ip', label: '102.88.14.19', type: 'ip', risk: 'critical', x: 72, y: 26 }
    ],
    graph_edges: [
      { from: 'inc-crd-u', to: 'inc-crd-h', label: 'login_from' },
      { from: 'inc-crd-ip', to: 'inc-crd-u', label: 'credential_access' }
    ],
    owner: 'Riley Grant',
    entity: 'acct-payroll-09',
    eventType: 'Credential Abuse',
    affected: '1 host, 1 privileged user',
    confidence: '0.94',
    users: ['jane.carter'],
    hosts: ['acct-payroll-09'],
    mitre: ['TA0006 Credential Access', 'TA0001 Initial Access'],
    evidence: [
      { title: 'Authentication deviation', content: 'Login geography and device fingerprint both deviated from the 30-day user profile.' },
      { title: 'Risk correlation', content: 'Privilege token issuance followed directly after abnormal MFA approval pattern.' },
      { title: 'Suggested action', content: 'Reset credentials, revoke tokens, and validate payroll admin entitlements.' }
    ]
  },
  {
    id: 'INC-LAT-403',
    title: 'Lateral movement chain crossing payments segment',
    severity: 'High',
    status: 'INVESTIGATING',
    assigned_to: 'Maya Patel',
    mitre_stage: 'TA0008 Lateral Movement',
    anomaly_score: 0.89,
    risk_score: 86,
    created_at: '2026-03-26 09:38:05',
    entities: ['svc-payments-admin', 'dc-east-02', '10.11.4.20'],
    timeline: [
      { time: '09:38', title: 'Remote admin execution', detail: 'Administrative command execution observed across segmented hosts.' },
      { time: '09:42', title: 'Credential reuse pattern', detail: 'Service account token reused on domain controller path.' },
      { time: '09:47', title: 'Chain confidence increased', detail: 'Attack graph linked two separate admin events into one path.' }
    ],
    graph_nodes: [
      { id: 'inc-lat-u', label: 'svc-payments-admin', type: 'user', risk: 'high', x: 20, y: 34 },
      { id: 'inc-lat-h1', label: 'payments-app-02', type: 'host', risk: 'high', x: 46, y: 28 },
      { id: 'inc-lat-h2', label: 'dc-east-02', type: 'host', risk: 'critical', x: 70, y: 46 }
    ],
    graph_edges: [
      { from: 'inc-lat-u', to: 'inc-lat-h1', label: 'executed_on' },
      { from: 'inc-lat-h1', to: 'inc-lat-h2', label: 'lateral_move' }
    ],
    owner: 'Maya Patel',
    entity: 'dc-east-02',
    eventType: 'Lateral Movement',
    affected: '2 hosts, 1 service account',
    confidence: '0.89',
    users: ['svc-payments-admin'],
    hosts: ['payments-app-02', 'dc-east-02'],
    mitre: ['TA0008 Lateral Movement', 'TA0004 Privilege Escalation'],
    evidence: [
      { title: 'Execution evidence', content: 'Remote administration chain deviated from approved payment maintenance pattern.' },
      { title: 'Graph evidence', content: 'Entity graph links admin token reuse to east domain controller access.' },
      { title: 'Response guidance', content: 'Constrain service account and inspect remote management tooling lineage.' }
    ]
  },
  {
    id: 'INC-INS-404',
    title: 'Insider anomaly on customer export workflow',
    severity: 'High',
    status: 'OPEN',
    assigned_to: 'Unassigned',
    mitre_stage: 'TA0010 Exfiltration',
    anomaly_score: 0.83,
    risk_score: 78,
    created_at: '2026-03-26 09:54:11',
    entities: ['aarav.mehra', 'cust-export-01', '198.51.100.22'],
    timeline: [
      { time: '09:54', title: 'Export volume deviation', detail: 'Data export volume rose well above the user’s monthly baseline.' },
      { time: '09:58', title: 'Off-hours access', detail: 'Access occurred outside approved customer analytics schedule.' },
      { time: '10:03', title: 'External transfer attempt', detail: 'Compressed archive prepared for unapproved destination.' }
    ],
    graph_nodes: [
      { id: 'inc-ins-u', label: 'aarav.mehra', type: 'user', risk: 'high', x: 18, y: 38 },
      { id: 'inc-ins-h', label: 'cust-export-01', type: 'host', risk: 'high', x: 46, y: 46 },
      { id: 'inc-ins-ip', label: '198.51.100.22', type: 'ip', risk: 'medium', x: 74, y: 30 }
    ],
    graph_edges: [
      { from: 'inc-ins-u', to: 'inc-ins-h', label: 'executed_on' },
      { from: 'inc-ins-h', to: 'inc-ins-ip', label: 'connected_to' }
    ],
    owner: 'Unassigned',
    entity: 'cust-export-01',
    eventType: 'Insider Anomaly',
    affected: '1 host, 1 user',
    confidence: '0.83',
    users: ['aarav.mehra'],
    hosts: ['cust-export-01'],
    mitre: ['TA0010 Exfiltration'],
    evidence: [
      { title: 'Volume deviation', content: 'Customer export size exceeded the user baseline by 6.2x.' },
      { title: 'Timing anomaly', content: 'Sequence began outside normal operating hours and without peer activity.' },
      { title: 'Analyst action', content: 'Validate business justification before approving any outbound transfer.' }
    ]
  },
  {
    id: 'INC-PHS-405',
    title: 'Phishing escalation leading to suspicious attachment access',
    severity: 'High',
    status: 'OPEN',
    assigned_to: 'Jordan Lee',
    mitre_stage: 'TA0001 Initial Access',
    anomaly_score: 0.81,
    risk_score: 74,
    created_at: '2026-03-26 10:04:20',
    entities: ['maya.patel', 'mail-gateway-01', '44.213.20.77'],
    timeline: [
      { time: '10:04', title: 'Email AI flagged lure', detail: 'Urgency and impersonation patterns exceeded phishing threshold.' },
      { time: '10:07', title: 'Attachment opened', detail: 'Attachment opened on a device without prior sender relationship.' },
      { time: '10:10', title: 'Follow-on URL access', detail: 'Embedded link visited shortly after attachment execution.' }
    ],
    graph_nodes: [
      { id: 'inc-phs-u', label: 'maya.patel', type: 'user', risk: 'high', x: 18, y: 26 },
      { id: 'inc-phs-h', label: 'mail-gateway-01', type: 'host', risk: 'medium', x: 44, y: 42 },
      { id: 'inc-phs-ip', label: '44.213.20.77', type: 'ip', risk: 'high', x: 70, y: 28 }
    ],
    graph_edges: [
      { from: 'inc-phs-ip', to: 'inc-phs-h', label: 'connected_to' },
      { from: 'inc-phs-h', to: 'inc-phs-u', label: 'delivery' }
    ],
    owner: 'Jordan Lee',
    entity: 'mail-gateway-01',
    eventType: 'Phishing Escalation',
    affected: '1 user, 1 mail asset',
    confidence: '0.81',
    users: ['maya.patel'],
    hosts: ['mail-gateway-01'],
    mitre: ['TA0001 Initial Access', 'TA0002 Execution'],
    evidence: [
      { title: 'Email signal', content: 'Sender entropy and urgency language indicate probable phishing lure.' },
      { title: 'Attachment risk', content: 'Attachment access chain matched known malicious delivery pattern.' },
      { title: 'Response', content: 'Quarantine related emails and inspect downstream URL telemetry.' }
    ]
  }
];

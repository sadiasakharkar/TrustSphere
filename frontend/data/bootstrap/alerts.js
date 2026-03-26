export const bootstrapAlerts = [
  { id: 'ALT-7001', source: 'Firewall', severity: 'Critical', title: 'Outbound C2 beacon pattern from treasury segment', timestamp: '2026-03-26 10:11:08', entity: 'treasury-ws-04', status: 'Active' },
  { id: 'ALT-7002', source: 'IAM', severity: 'High', title: 'Impossible travel login for payroll admin', timestamp: '2026-03-26 10:09:44', entity: 'jane.carter', status: 'Investigating' },
  { id: 'ALT-7003', source: 'Endpoint', severity: 'Critical', title: 'Unsigned encryptor executed from user profile', timestamp: '2026-03-26 10:08:27', entity: 'treasury-ws-04', status: 'Contained' },
  { id: 'ALT-7004', source: 'Transaction Anomaly', severity: 'High', title: 'Abnormal transfer sequence from wire service account', timestamp: '2026-03-26 10:06:15', entity: 'svc-wire-transfer', status: 'Active' },
  { id: 'ALT-7005', source: 'URL AI', severity: 'Medium', title: 'Suspicious credential harvesting domain accessed', timestamp: '2026-03-26 10:03:49', entity: 'branch-kiosk-03', status: 'Open' },
  { id: 'ALT-7006', source: 'Credential AI', severity: 'High', title: 'Exposed access key found in internal paste', timestamp: '2026-03-26 09:59:58', entity: 'git-internal-01', status: 'Investigating' }
];

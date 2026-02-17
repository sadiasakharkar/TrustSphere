export const metrics = [
  { label: 'Total Alerts Today', value: 482, delta: '+12.8%' },
  { label: 'Critical Alerts', value: 37, delta: '+4.2%' },
  { label: 'Mean Time to Detect', value: '11m 24s', delta: '-9.1%' },
  { label: 'Open Incidents', value: 19, delta: '+2.0%' }
];

export const anomalyTrend = [22, 19, 27, 31, 28, 35, 40, 34, 42, 49, 46, 52];

export const severityDistribution = [14, 26, 34, 18, 8];

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
    host: 'acct-payroll-09',
    alertType: 'Privilege Escalation',
    riskScore: 92,
    status: 'Investigating',
    severity: 'Critical'
  },
  {
    id: 'INC-21404',
    timestamp: '2026-02-17 10:41:58',
    host: 'teller-branch-11',
    alertType: 'Anomalous Login',
    riskScore: 78,
    status: 'Open',
    severity: 'High'
  },
  {
    id: 'INC-21405',
    timestamp: '2026-02-17 11:02:42',
    host: 'loan-underwrite-03',
    alertType: 'Malware Signature',
    riskScore: 71,
    status: 'Contained',
    severity: 'High'
  },
  {
    id: 'INC-21406',
    timestamp: '2026-02-17 11:27:06',
    host: 'atm-cluster-02',
    alertType: 'Data Exfiltration',
    riskScore: 88,
    status: 'Escalated',
    severity: 'Critical'
  },
  {
    id: 'INC-21407',
    timestamp: '2026-02-17 12:05:17',
    host: 'compliance-reports-01',
    alertType: 'Phishing',
    riskScore: 56,
    status: 'Open',
    severity: 'Medium'
  }
];

export const analyticsTrend = [9, 11, 13, 10, 17, 21, 18, 23, 20, 26, 24, 29];

export const anomalousEntities = [
  { entity: 'acct-payroll-09', type: 'Host', score: 96, events: 42 },
  { entity: 'jane.carter', type: 'User', score: 91, events: 33 },
  { entity: 'teller-branch-11', type: 'Host', score: 86, events: 29 },
  { entity: 'svc-wire-transfer', type: 'User', score: 81, events: 24 },
  { entity: 'atm-cluster-02', type: 'Host', score: 77, events: 18 }
];

export const users = [
  { id: 'U-001', name: 'Avery Collins', role: 'Analyst', status: 'Active' },
  { id: 'U-002', name: 'Maya Patel', role: 'Admin', status: 'Active' },
  { id: 'U-003', name: 'Jordan Lee', role: 'Analyst', status: 'Suspended' },
  { id: 'U-004', name: 'Riley Grant', role: 'Analyst', status: 'Active' }
];

export const playbookSteps = [
  { title: 'Containment', detail: 'Isolate impacted hosts and revoke suspicious sessions.' },
  { title: 'Investigation', detail: 'Correlate SIEM logs, EDR telemetry, and IAM changes.' },
  { title: 'Eradication', detail: 'Remove malicious binaries and patch exploited vectors.' },
  { title: 'Recovery', detail: 'Restore services with validation checks and monitoring.' },
  { title: 'Escalation', detail: 'Notify SOC lead, risk office, and regulatory liaison.' }
];

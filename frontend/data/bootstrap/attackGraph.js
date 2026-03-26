export const bootstrapAttackGraph = {
  nodes: [
    { id: 'g-u1', label: 'jane.carter', type: 'user', risk: 'critical', x: 14, y: 40 },
    { id: 'g-h1', label: 'acct-payroll-09', type: 'host', risk: 'high', x: 34, y: 28 },
    { id: 'g-p1', label: 'powershell.exe', type: 'process', risk: 'high', x: 54, y: 42 },
    { id: 'g-ip1', label: '102.88.14.19', type: 'ip', risk: 'critical', x: 74, y: 26 },
    { id: 'g-db1', label: 'payroll-db', type: 'database', risk: 'critical', x: 86, y: 54 }
  ],
  edges: [
    { from: 'g-u1', to: 'g-h1', label: 'login_from' },
    { from: 'g-h1', to: 'g-p1', label: 'executed_on' },
    { from: 'g-p1', to: 'g-ip1', label: 'connected_to' },
    { from: 'g-ip1', to: 'g-db1', label: 'lateral_move' }
  ],
  chains: [
    { id: 'CHAIN-301', title: 'Initial access to exfiltration path', severity: 'Critical', confidence: '0.95' }
  ],
  attackStages: [
    'Initial Access',
    'Credential Access',
    'Privilege Escalation',
    'Lateral Movement',
    'Exfiltration'
  ]
};

export const bootstrapMetrics = {
  topRow: [
    { label: 'Active Threats', value: 12, delta: '+3', status: 'critical', helper: 'Bootstrap incident queue' },
    { label: 'Risk Index', value: 87, delta: '+6%', status: 'high', helper: 'Composite platform risk' },
    { label: 'MTTD', value: '06m', delta: '-1m', status: 'healthy', helper: 'Mean time to detect' },
    { label: 'MTTR', value: '19m', delta: '-2m', status: 'healthy', helper: 'Mean time to respond' },
    { label: 'Alert Reduction', value: '38%', delta: '+4%', status: 'healthy', helper: 'AI-assisted triage compression' }
  ],
  severityDistribution: {
    Critical: 4,
    High: 5,
    Medium: 2,
    Low: 1
  },
  detectionConfidence: 0.94,
  systemStatus: 'Nominal',
  riskTrend: [62, 66, 71, 69, 74, 79, 82, 85, 83, 87, 90, 88]
};

export const bootstrapPlaybooks = [
  {
    id: 'PB-9001',
    name: 'Credential containment workflow',
    triggerReason: 'Privilege token issued after impossible-travel login',
    aiConfidence: 0.94,
    automationStatus: 'Ready',
    steps: [
      { title: 'Reset user credentials', detail: 'Revoke active sessions and invalidate privileged tokens.', owner: 'IAM Team', confidence: 96 },
      { title: 'Isolate impacted endpoint', detail: 'Restrict host from east-west movement while evidence is preserved.', owner: 'SOC Tier-1', confidence: 93 },
      { title: 'Review graph pivots', detail: 'Confirm whether adjacent hosts share the same authentication chain.', owner: 'Threat Hunt', confidence: 89 }
    ]
  },
  {
    id: 'PB-9002',
    name: 'Ransomware suppression workflow',
    triggerReason: 'Unsigned encryptor with file rename spike detected on treasury workstation',
    aiConfidence: 0.97,
    automationStatus: 'Pending approval',
    steps: [
      { title: 'Block malicious process tree', detail: 'Terminate descendant processes and preserve memory capture.', owner: 'EDR Team', confidence: 97 },
      { title: 'Protect backup assets', detail: 'Verify backup shares remain isolated and unmodified.', owner: 'Platform Ops', confidence: 91 },
      { title: 'Scope adjacent blast radius', detail: 'Search for matching hashes and rename behavior across finance endpoints.', owner: 'IR Lead', confidence: 94 }
    ]
  }
];

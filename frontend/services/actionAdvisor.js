function toTitleCase(value = '') {
  return String(value)
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function normalizeSeverity(severity = '') {
  const value = String(severity).toLowerCase();
  if (value.includes('critical')) return 'critical';
  if (value.includes('high')) return 'high';
  if (value.includes('medium')) return 'medium';
  if (value.includes('low')) return 'low';
  return 'medium';
}

function severityWeight(severity = '') {
  switch (normalizeSeverity(severity)) {
    case 'critical':
      return 12;
    case 'high':
      return 7;
    case 'medium':
      return 3;
    default:
      return 1;
  }
}

function buildAction(id, label, detail) {
  return {
    id,
    label,
    detail,
    type: 'status',
    status: 'INVESTIGATING',
    playbookHint: '',
    confidence: 80,
    effectiveness: 70,
    disruption: 35,
    urgency: 75,
    reversibility: 60,
    rationale: '',
    tradeoff: '',
    whyNotBest: ''
  };
}

function getScenarioActions(incident, recommended = []) {
  const title = `${incident?.summary?.title || incident?.title || ''} ${incident?.summary?.mitre?.join(' ') || incident?.mitre?.join(' ') || ''}`.toLowerCase();
  const severity = incident?.summary?.severity || incident?.severity || 'Medium';
  const baseRecommendations = recommended.length ? recommended : [];

  if (title.includes('ransom') || title.includes('encrypt')) {
    return [
      {
        ...buildAction('isolate-endpoint', 'Isolate endpoint', 'Contain the impacted workstation immediately to stop encryption spread and preserve evidence.'),
        status: 'CONTAINED',
        playbookHint: 'Ransomware suppression workflow',
        confidence: 97,
        effectiveness: 96,
        disruption: 62,
        urgency: 99,
        reversibility: 58,
        rationale: 'The host already shows impact-stage behavior, so containment outranks observation or network-only blocking.',
        tradeoff: 'This can interrupt the user session and may pause legitimate finance operations on the endpoint.'
      },
      {
        ...buildAction('block-process-tree', 'Block malicious process tree', 'Terminate the suspected encryptor lineage and preserve volatile state for forensics.'),
        status: 'INVESTIGATING',
        playbookHint: 'Ransomware suppression workflow',
        confidence: 93,
        effectiveness: 90,
        disruption: 48,
        urgency: 94,
        reversibility: 63,
        rationale: 'Stopping the executing process reduces ongoing damage but does not fully prevent lateral propagation.',
        tradeoff: 'Process termination can lose volatile forensic context.'
      },
      {
        ...buildAction('protect-backups', 'Protect backup assets', 'Verify backup shares remain isolated before the threat can pivot to recovery infrastructure.'),
        status: 'INVESTIGATING',
        playbookHint: 'Ransomware suppression workflow',
        confidence: 88,
        effectiveness: 82,
        disruption: 28,
        urgency: 86,
        reversibility: 92,
        rationale: 'This limits business impact if encryption expands, but it does not remove the active threat from the host.',
        tradeoff: 'Backup access controls may slow emergency restore workflows.'
      }
    ];
  }

  if (title.includes('credential') || title.includes('mfa') || title.includes('identity')) {
    return [
      {
        ...buildAction('revoke-identity', 'Reset credentials and revoke tokens', 'Invalidate current sessions and rotate the impacted identity before more privileged actions occur.'),
        status: 'CONTAINED',
        playbookHint: 'Credential containment workflow',
        confidence: 95,
        effectiveness: 93,
        disruption: 54,
        urgency: 96,
        reversibility: 57,
        rationale: 'Identity abuse is still active, and revoking sessions removes the attacker from the primary control plane fastest.',
        tradeoff: 'The user will lose access immediately and downstream jobs may fail until access is restored.'
      },
      {
        ...buildAction('isolate-host', 'Isolate affected host', 'Contain the endpoint linked to the privileged session while validation continues.'),
        status: 'CONTAINED',
        playbookHint: 'Credential containment workflow',
        confidence: 89,
        effectiveness: 84,
        disruption: 61,
        urgency: 88,
        reversibility: 59,
        rationale: 'Useful if host compromise is suspected, but identity control is still the more urgent lever.',
        tradeoff: 'Can disrupt payroll or admin activity even if the account is the primary compromise vector.'
      },
      {
        ...buildAction('escalate-identity', 'Escalate to IAM and IR lead', 'Trigger coordinated review for privileged entitlements, approvals, and downstream blast radius.'),
        type: 'status',
        status: 'ESCALATED',
        confidence: 84,
        effectiveness: 76,
        disruption: 12,
        urgency: 78,
        reversibility: 100,
        rationale: 'Escalation improves coordination but does not directly remove attacker access.',
        tradeoff: 'Adds people quickly, but can delay decisive containment if used instead of a direct response.'
      }
    ];
  }

  if (title.includes('phishing') || title.includes('email') || title.includes('attachment')) {
    return [
      {
        ...buildAction('quarantine-email', 'Quarantine related emails', 'Remove the lure from inboxes and stop additional users from interacting with the campaign.'),
        status: 'CONTAINED',
        playbookHint: 'Email containment workflow',
        confidence: 92,
        effectiveness: 88,
        disruption: 22,
        urgency: 91,
        reversibility: 85,
        rationale: 'This reduces spread quickly and protects the rest of the environment while endpoint review continues.',
        tradeoff: 'Legitimate-but-similar email threads may be temporarily affected.'
      },
      {
        ...buildAction('disable-account', 'Disable impacted user account', 'Temporarily suspend the user while access and phishing follow-on actions are investigated.'),
        status: 'CONTAINED',
        confidence: 83,
        effectiveness: 79,
        disruption: 58,
        urgency: 82,
        reversibility: 62,
        rationale: 'Strong containment if credentials are compromised, but heavier than needed when the primary risk is email spread.',
        tradeoff: 'This can interrupt the user if the campaign has not yet reached credential compromise.'
      },
      {
        ...buildAction('escalate-phishing', 'Escalate to analyst review', 'Preserve the message, attachment, and downstream URL path for deeper analysis.'),
        status: 'ESCALATED',
        confidence: 80,
        effectiveness: 68,
        disruption: 8,
        urgency: 73,
        reversibility: 100,
        rationale: 'Good for evidence quality, but slower than direct quarantine when the lure is still active.',
        tradeoff: 'Adds confidence without reducing exposure immediately.'
      }
    ];
  }

  if (title.includes('lateral') || title.includes('remote admin') || title.includes('service account')) {
    return [
      {
        ...buildAction('constrain-account', 'Constrain service account access', 'Reduce token scope and lateral movement permissions while validating the attack chain.'),
        status: 'CONTAINED',
        playbookHint: 'Credential containment workflow',
        confidence: 91,
        effectiveness: 90,
        disruption: 49,
        urgency: 94,
        reversibility: 60,
        rationale: 'The active chain depends on reused credentials, so reducing account privileges cuts off the pivot path.',
        tradeoff: 'Operational automations using the account may pause until reviewed.'
      },
      {
        ...buildAction('segment-hosts', 'Restrict remote administration channels', 'Tighten east-west management access between the affected hosts.'),
        status: 'CONTAINED',
        confidence: 86,
        effectiveness: 85,
        disruption: 43,
        urgency: 87,
        reversibility: 70,
        rationale: 'Network restriction slows propagation, but it may not stop already-issued tokens.',
        tradeoff: 'Maintenance workflows and legitimate admin tooling may be delayed.'
      },
      {
        ...buildAction('escalate-hunt', 'Escalate to threat hunt', 'Search the wider estate for the same movement chain and neighboring entities.'),
        status: 'ESCALATED',
        confidence: 82,
        effectiveness: 72,
        disruption: 10,
        urgency: 76,
        reversibility: 100,
        rationale: 'This increases visibility, but direct access reduction is still the fastest containment lever.',
        tradeoff: 'Useful for scoping, not immediate containment.'
      }
    ];
  }

  const actions = baseRecommendations.map((label, index) => ({
    ...buildAction(`recommended-${index}`, label, `${label} based on current severity, evidence stack, and workflow context.`),
    confidence: clamp(88 - index * 5, 68, 96),
    effectiveness: clamp(90 - index * 6, 62, 95),
    disruption: clamp(34 + index * 8, 18, 78),
    urgency: clamp(92 - index * 7, 60, 96),
    reversibility: clamp(78 - index * 4, 48, 90),
    rationale: `${label} aligns with the evidence currently surfaced in the case narrative and model confidence.`,
    tradeoff: 'This action is relevant, but lower-ranked options either act slower or create more disruption.'
  }));

  if (actions.length) return actions;

  const defaultAction = buildAction('investigate', 'Continue guided investigation', 'Keep the case in active investigation while more evidence is collected.');
  defaultAction.status = severityWeight(severity) >= 7 ? 'INVESTIGATING' : 'OPEN';
  defaultAction.confidence = 76;
  defaultAction.effectiveness = 67;
  defaultAction.urgency = 70;
  defaultAction.reversibility = 94;
  defaultAction.rationale = 'The incident lacks a narrow response signal, so investigation remains the safest next step.';
  defaultAction.tradeoff = 'This avoids premature disruption but leaves the incident active for longer.';
  return [defaultAction];
}

function scoreAction(action, severity = 'Medium') {
  return clamp(
    (action.effectiveness * 0.36)
      + (action.confidence * 0.26)
      + (action.urgency * 0.24)
      + (action.reversibility * 0.14)
      - (action.disruption * 0.18)
      + severityWeight(severity),
    1,
    99
  );
}

export function deriveIncidentActionPlan(incident, playbooks = []) {
  const severity = incident?.summary?.severity || incident?.severity || 'Medium';
  const recommended = incident?.recommended_actions || incident?.llm?.recommended_actions || [];
  const actions = getScenarioActions(incident, recommended)
    .map((action) => ({ ...action, score: scoreAction(action, severity) }))
    .sort((a, b) => b.score - a.score)
    .map((action, index, list) => ({
      ...action,
      whyNotBest: index === 0
        ? 'Best fit for the current evidence, urgency, and business-risk balance.'
        : `Ranked below ${list[0].label} because it is either slower to contain the threat or more disruptive for the same confidence level.`
    }));

  const recommendedAction = actions[0];
  const matchedPlaybook = playbooks.find((playbook) => {
    const haystack = `${playbook?.name || ''} ${playbook?.triggerReason || ''}`.toLowerCase();
    return recommendedAction?.playbookHint && haystack.includes(recommendedAction.playbookHint.toLowerCase().split(' ')[0]);
  }) || playbooks[0] || null;

  return {
    recommendedAction,
    alternatives: actions.slice(1),
    comparison: actions,
    recommendedPlaybook: matchedPlaybook,
    reasoningSummary: recommendedAction
      ? `${recommendedAction.label} is the strongest next move because it best balances containment speed, analyst confidence, and acceptable business disruption.`
      : 'No action recommendation is available yet.'
  };
}

export function deriveRealtimeSummary(incidents = [], lastEvent = null) {
  const criticalCount = incidents.filter((item) => normalizeSeverity(item.severity || item?.summary?.severity) === 'critical').length;
  const openCount = incidents.filter((item) => {
    const value = String(item.status || item?.summary?.status || '').toLowerCase();
    return !value.includes('resolved');
  }).length;
  const topIncident = [...incidents]
    .sort((a, b) => Number(b.riskScore || b.risk_score || 0) - Number(a.riskScore || a.risk_score || 0))[0];
  const topActionPlan = topIncident ? deriveIncidentActionPlan(topIncident) : null;

  return {
    total: incidents.length,
    criticalCount,
    openCount,
    topIncident,
    topAction: topActionPlan?.recommendedAction || null,
    lastEventLabel: lastEvent?.payload?.incident?.title || lastEvent?.payload?.title || lastEvent?.type || 'Awaiting live incident updates'
  };
}

export function deriveResponseFeed(incidents = []) {
  return incidents.slice(0, 4).map((incident) => {
    const plan = deriveIncidentActionPlan(incident);
    return {
      id: incident.id || incident?.summary?.id,
      incidentId: incident.id || incident?.summary?.id,
      title: incident.title || incident?.summary?.title || 'Active incident',
      severity: incident.severity || incident?.summary?.severity || 'Medium',
      status: incident.status || incident?.summary?.status || 'OPEN',
      entity: incident.entity || incident?.summary?.hosts?.[0] || incident?.summary?.users?.[0] || 'Unknown asset',
      action: plan.recommendedAction?.label || 'Continue investigation',
      rationale: plan.recommendedAction?.rationale || 'Evidence is still being compiled for this case.',
      score: plan.recommendedAction?.score || 0
    };
  });
}

export function formatActionLabel(value = '') {
  return toTitleCase(value);
}

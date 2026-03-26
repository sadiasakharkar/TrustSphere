import { apiRequest } from './apiClient';

const EMAIL_HISTORY_KEY = 'trustsphere.email.history';
const FALLBACK_INBOX = [
  {
    id: 'mail-001',
    sender: 'bank@secure.com',
    subject: 'Verify your account urgently',
    body: 'Click http://fake-bank.xyz and enter password immediately to keep your banking access active.',
  },
  {
    id: 'mail-002',
    sender: 'hr@company.com',
    subject: 'Salary Update',
    body: 'Please review your salary details in the attached document and confirm the latest compensation breakdown.',
  },
  {
    id: 'mail-003',
    sender: 'support@paypal.com',
    subject: 'Unusual login detected',
    body: 'We noticed a suspicious login. Verify now at http://phishing-login.xyz to secure your account.',
  },
];

function readFallbackHistory() {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(window.localStorage.getItem(EMAIL_HISTORY_KEY) || '[]');
  } catch {
    return [];
  }
}

function writeFallbackHistory(history) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(EMAIL_HISTORY_KEY, JSON.stringify(history));
}

function fallbackAnalyze({ input, subject = '', sender = 'unknown@example.com' }) {
  const text = String(input || '').toLowerCase();
  const suspiciousHits = [
    'urgent',
    'verify',
    'password',
    'login',
    'click http',
    'gift card',
    'wire',
  ].filter((token) => text.includes(token)).length;
  const probability = Math.min(0.18 + suspiciousHits * 0.14, 0.98);
  const severity = probability >= 0.75 ? 'HIGH' : probability >= 0.4 ? 'MEDIUM' : 'LOW';
  const actions = severity === 'HIGH'
    ? ['Escalate to SOC analyst', 'Quarantine suspicious email', 'Block sender and embedded domains']
    : severity === 'MEDIUM'
      ? ['Flag email for analyst review', 'Warn recipient before interaction']
      : ['Log event for monitoring'];

  const entry = {
    input,
    sender,
    subject: subject || 'Analyzed email',
    risk_score: Number((probability * 100).toFixed(2)),
    severity,
    models: { email_detector: Number(probability.toFixed(4)) },
    actions,
    time: new Date().toISOString(),
    label: probability >= 0.5 ? 'phishing' : 'safe',
  };

  writeFallbackHistory([...readFallbackHistory(), entry]);

  return {
    risk_score: entry.risk_score,
    severity: entry.severity,
    models: entry.models,
    actions_taken: entry.actions,
    label: entry.label,
  };
}

export async function analyzeEmail(input, meta = {}) {
  const { data } = await apiRequest('/api/email/analyze', {
    method: 'POST',
    body: JSON.stringify({ input, subject: meta.subject || '', sender: meta.sender || 'unknown@example.com' }),
    fallbackData: () => fallbackAnalyze({ input, subject: meta.subject, sender: meta.sender }),
  });
  return data;
}

export async function getInboxEmails() {
  const { data } = await apiRequest('/api/email/inbox', {
    fallbackData: FALLBACK_INBOX,
  });
  return data;
}

export async function getEmailHistory() {
  const { data } = await apiRequest('/api/email/history', {
    fallbackData: () => [...readFallbackHistory()].reverse(),
  });
  return data;
}

export async function clearEmailHistory() {
  const { data } = await apiRequest('/api/email/history', {
    method: 'DELETE',
    fallbackData: () => {
      writeFallbackHistory([]);
      return { status: 'cleared' };
    },
  });
  return data;
}

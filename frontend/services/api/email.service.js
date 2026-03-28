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
  const tokens = [
    'urgent',
    'verify',
    'password',
    'login',
    'click http',
    'gift card',
    'wire',
    'otp',
    'account',
  ];
  const matchedTokens = tokens.filter((token) => text.includes(token));
  const suspiciousHits = matchedTokens.length;
  const probability = Math.min(0.18 + suspiciousHits * 0.14, 0.98);
  const severity = probability >= 0.75 ? 'HIGH' : probability >= 0.4 ? 'MEDIUM' : 'LOW';
  const actions = severity === 'HIGH'
    ? ['Escalate to SOC analyst', 'Quarantine suspicious email', 'Block sender and embedded domains']
    : severity === 'MEDIUM'
      ? ['Flag email for analyst review', 'Warn recipient before interaction']
      : ['Log event for monitoring'];
  const reasons = [
    ...(text.includes('http') || text.includes('login') || text.includes('verify') ? ['Suspicious account verification or login lure detected'] : []),
    ...(text.includes('urgent') || text.includes('immediately') ? ['Urgent language is pressuring the recipient to act quickly'] : []),
    ...(text.includes('password') || text.includes('otp') || text.includes('credentials') ? ['Credential harvesting language detected'] : []),
    ...(probability >= 0.6 ? ['The email classifier produced an elevated phishing score'] : []),
  ];

  const entry = {
    input,
    sender,
    subject: subject || 'Analyzed email',
    risk_score: Number((probability * 100).toFixed(2)),
    severity,
    models: { email_detector: Number(probability.toFixed(4)) },
    actions,
    risk_drivers: [
      ...matchedTokens,
      ...(probability > 0.6 ? ['email_detector anomaly'] : []),
    ],
    reasons: reasons.length ? reasons : [severity === 'LOW' ? 'No major phishing indicators were found' : 'High-risk content patterns were detected across the message'],
    time: new Date().toISOString(),
    label: probability >= 0.5 ? 'phishing' : 'safe',
  };

  writeFallbackHistory([...readFallbackHistory(), entry]);

  return {
    risk_score: entry.risk_score,
    severity: entry.severity,
    models: entry.models,
    actions_taken: entry.actions,
    risk_drivers: entry.risk_drivers,
    reasons: entry.reasons,
    subject: entry.subject,
    sender: entry.sender,
    label: entry.label,
  };
}

export async function analyzeEmail(input, meta = {}) {
  try {
    const { data } = await apiRequest('/api/email/analyze', {
      method: 'POST',
      body: JSON.stringify({ input, subject: meta.subject || '', sender: meta.sender || 'unknown@example.com' }),
      fallbackData: () => fallbackAnalyze({ input, subject: meta.subject, sender: meta.sender }),
    });
    return data;
  } catch {
    return fallbackAnalyze({ input, subject: meta.subject, sender: meta.sender });
  }
}

export async function getInboxEmails() {
  try {
    const { data } = await apiRequest('/api/email/inbox', {
      fallbackData: FALLBACK_INBOX,
    });
    return data;
  } catch {
    return FALLBACK_INBOX;
  }
}

export async function getEmailHistory() {
  try {
    const { data } = await apiRequest('/api/email/history', {
      fallbackData: () => [...readFallbackHistory()].reverse(),
    });
    return data;
  } catch {
    return [...readFallbackHistory()].reverse();
  }
}

export async function clearEmailHistory() {
  try {
    const { data } = await apiRequest('/api/email/history', {
      method: 'DELETE',
      fallbackData: () => {
        writeFallbackHistory([]);
        return { status: 'cleared' };
      },
    });
    return data;
  } catch {
    writeFallbackHistory([]);
    return { status: 'cleared' };
  }
}

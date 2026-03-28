import Link from 'next/link';
import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import EmailHistoryTable from '../components/soc/EmailHistoryTable';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { analyzeEmail, clearEmailHistory, getEmailHistory, getInboxEmails } from '../services/api/email.service';

function mapHistory(items = []) {
  return items.map((entry, index) => ({
    id: `${entry.time || 'history'}-${index}`,
    subject: entry.subject || entry.input || 'Analyzed email',
    sender: entry.sender || 'unknown@example.com',
    bodySnippet: entry.input || '',
    risk: entry.risk_score,
    severity: entry.severity,
    actions: entry.actions || [],
    reasons: entry.reasons || [],
    riskDrivers: entry.risk_drivers || [],
    time: entry.time || 'Unknown'
  }));
}

function triggerSeverityToast(result) {
  const severity = String(result?.severity || '').toUpperCase();
  const risk = Number(result?.risk_score || 0).toFixed(2);
  if (severity === 'HIGH') {
    toast.error(`High risk threat detected. Score: ${risk}`);
  } else if (severity === 'MEDIUM') {
    toast.warning(`Suspicious activity detected. Score: ${risk}`);
  }
}

export default function EmailPage() {
  const [emails, setEmails] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [emailInput, setEmailInput] = useState('');
  const [manualSubject, setManualSubject] = useState('');
  const [manualSender, setManualSender] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchEmails = async () => {
    try {
      const inbox = await getInboxEmails();
      setEmails(inbox);
      setSelectedEmail((current) => current || inbox[0] || null);
      setError('');
    } catch (err) {
      setError(err.message || 'Unable to load inbox.');
    }
  };

  const fetchHistory = async () => {
    try {
      const entries = await getEmailHistory();
      setHistory(mapHistory(entries));
      setError('');
    } catch (err) {
      setError(err.message || 'Unable to load email history.');
    }
  };

  useEffect(() => {
    fetchEmails();
    fetchHistory();
  }, []);

  const handleAnalyze = async (emailRecord = selectedEmail) => {
    if (!emailRecord?.body) {
      setError('Select an inbox email before running analysis.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      setSelectedEmail(emailRecord);
      const nextResult = await analyzeEmail(emailRecord.body, {
        subject: emailRecord.subject,
        sender: emailRecord.sender,
      });
      setResult(nextResult);
      triggerSeverityToast(nextResult);
      await fetchHistory();
    } catch (err) {
      setError(err.message || 'Unable to analyze email.');
    } finally {
      setLoading(false);
    }
  };

  const handleManualAnalyze = async () => {
    if (!emailInput.trim()) {
      setError('Paste email content before running analysis.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const nextResult = await analyzeEmail(emailInput, {
        subject: manualSubject.trim() || 'Manual email submission',
        sender: manualSender.trim() || 'manual@local.demo',
      });
      setResult(nextResult);
      triggerSeverityToast(nextResult);
      setEmailInput('');
      setManualSubject('');
      setManualSender('');
      await fetchHistory();
    } catch (err) {
      setError(err.message || 'Unable to analyze pasted email content.');
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await clearEmailHistory();
      setHistory([]);
      setError('');
    } catch (err) {
      setError(err.message || 'Unable to clear email history.');
    }
  };

  const latestRisk = Number(result?.risk_score || 0);
  const latestReasons = result?.reasons || [];
  const latestDrivers = result?.risk_drivers || [];

  return (
    <RequireAuth>
      <Layout>
        <PageContainer>
          <PageHeader
            kicker="Email Analyzer"
            title="Email Analysis Module"
            description="Review incoming inbox messages, trigger email threat analysis with one click, and monitor persistent history like an enterprise SOC console."
            actions={<Link href="/overview" className="soc-btn-secondary">Back to overview</Link>}
          />

          <div className="space-y-6">
            <section className="grid gap-4 md:grid-cols-3">
              <div className="soc-panel-muted">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Inbox Coverage</p>
                <p className="mt-3 text-2xl font-semibold text-white">{emails.length}</p>
                <p className="mt-2 text-sm soc-text-muted">Messages ready for one-click analysis.</p>
              </div>
              <div className="soc-panel-muted">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Latest Severity</p>
                <div className="mt-3"><StatusBadge tone={result?.severity || 'default'}>{result?.severity || 'Awaiting scan'}</StatusBadge></div>
                <p className="mt-2 text-sm soc-text-muted">Current analyst verdict for the latest submission.</p>
              </div>
              <div className="soc-panel-muted">
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">History Entries</p>
                <p className="mt-3 text-2xl font-semibold text-white">{history.length}</p>
                <p className="mt-2 text-sm soc-text-muted">Persisted evidence for the current session.</p>
              </div>
            </section>

            <section className="soc-panel">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="soc-kicker">Manual Analysis</p>
                  <h2 className="mt-2 text-base font-semibold text-white">Paste email content</h2>
                  <p className="mt-2 text-sm leading-6 soc-text-muted">Paste suspicious email text here when you want to test a custom message outside the mock inbox.</p>
                </div>
                <button className="soc-btn-primary" onClick={handleManualAnalyze} disabled={loading}>
                  {loading ? 'Analyzing...' : 'Analyze pasted email'}
                </button>
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <input
                  className="w-full rounded-2xl border border-[rgba(65,71,85,0.45)] bg-[rgba(16,20,26,0.86)] px-4 py-3 text-sm text-white outline-none transition focus:border-[#4b8eff]"
                  placeholder="Subject line"
                  value={manualSubject}
                  onChange={(event) => setManualSubject(event.target.value)}
                />
                <input
                  className="w-full rounded-2xl border border-[rgba(65,71,85,0.45)] bg-[rgba(16,20,26,0.86)] px-4 py-3 text-sm text-white outline-none transition focus:border-[#4b8eff]"
                  placeholder="Sender address"
                  value={manualSender}
                  onChange={(event) => setManualSender(event.target.value)}
                />
              </div>

              <textarea
                className="mt-5 min-h-[180px] w-full rounded-2xl border border-[rgba(65,71,85,0.45)] bg-[rgba(16,20,26,0.86)] px-4 py-4 text-sm leading-7 text-white outline-none transition focus:border-[#4b8eff]"
                placeholder="Paste suspicious email content here..."
                value={emailInput}
                onChange={(event) => setEmailInput(event.target.value)}
              />

              {error ? <p className="mt-4 text-sm text-[#ffb3ad]">{error}</p> : null}
            </section>

            {result ? (
              <section className="soc-panel">
                <p className="soc-kicker">Result</p>
                <h2 className="mt-2 text-base font-semibold text-white">Latest email assessment</h2>
                <div className="mt-4 flex flex-wrap gap-2">
                  <StatusBadge tone={result.severity}>{result.severity}</StatusBadge>
                  <StatusBadge tone="medium">Risk {latestRisk.toFixed(2)}</StatusBadge>
                  <StatusBadge tone={result.label === 'phishing' ? 'high' : 'low'}>{result.label || 'unknown'}</StatusBadge>
                </div>
                <div className="mt-5 grid gap-4 xl:grid-cols-[0.8fr,1.2fr]">
                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Email Context</p>
                    <div className="mt-3 space-y-3 text-sm">
                      <div>
                        <p className="soc-text-muted">Subject</p>
                        <p className="mt-1 text-white">{result.subject || selectedEmail?.subject || manualSubject || 'Analyzed email'}</p>
                      </div>
                      <div>
                        <p className="soc-text-muted">Sender</p>
                        <p className="mt-1 text-white">{result.sender || selectedEmail?.sender || manualSender || 'unknown@example.com'}</p>
                      </div>
                    </div>
                  </div>
                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Why it was flagged</p>
                    <div className="mt-3 space-y-2">
                      {latestReasons.map((reason) => (
                        <p key={reason} className="text-sm leading-6 text-white">• {reason}</p>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="mt-4 grid gap-4 lg:grid-cols-[0.8fr,1.2fr]">
                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Model scores</p>
                    <div className="mt-3 space-y-2">
                      {Object.entries(result.models || {}).map(([name, score]) => (
                        <div key={name} className="flex items-center justify-between gap-3 text-sm">
                          <span className="text-white">{name}</span>
                          <span className="soc-text-muted">{Number(score).toFixed(3)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Detected indicators</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {latestDrivers.map((driver) => (
                        <span key={driver} className="soc-badge border border-[rgba(255,179,173,0.2)] bg-[rgba(255,179,173,0.08)] text-[#ffb3ad]">
                          {driver}
                        </span>
                      ))}
                    </div>
                    <p className="mt-5 text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Actions taken</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(result.actions_taken || []).map((action) => (
                        <span key={action} className="soc-badge border border-[rgba(65,71,85,0.55)] bg-[rgba(11,14,19,0.95)] text-[rgba(223,226,235,0.82)]">
                          {action}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </section>
            ) : null}

            <EmailHistoryTable history={history} onClear={handleClearHistory} />

            <section className="grid gap-6 xl:grid-cols-[0.85fr,1.15fr]">
              <section className="soc-panel">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="soc-kicker">Inbox</p>
                    <h2 className="mt-2 text-base font-semibold text-white">Incoming email stream</h2>
                  </div>
                  <StatusBadge tone="medium">{emails.length} loaded</StatusBadge>
                </div>
                <div className="mt-5 space-y-3">
                  {emails.map((mail) => {
                    const active = selectedEmail?.id === mail.id;
                    return (
                      <button
                        key={mail.id}
                        className={`w-full rounded-2xl border px-4 py-4 text-left transition ${active ? 'border-[#4b8eff] bg-[rgba(75,142,255,0.14)]' : 'border-[rgba(65,71,85,0.45)] bg-[rgba(16,20,26,0.86)] hover:border-[rgba(75,142,255,0.5)]'}`}
                        onClick={() => setSelectedEmail(mail)}
                      >
                        <p className="text-sm font-semibold text-white">{mail.sender}</p>
                        <p className="mt-1 text-sm leading-6 text-white">{mail.subject}</p>
                        <p className="mt-2 text-xs soc-text-muted">{mail.body.length > 96 ? `${mail.body.slice(0, 96)}...` : mail.body}</p>
                      </button>
                    );
                  })}
                </div>
              </section>

              <section className="soc-panel">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="soc-kicker">Selected Email</p>
                    <h2 className="mt-2 text-base font-semibold text-white">{selectedEmail?.subject || 'Choose an inbox email'}</h2>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      className="soc-btn-secondary"
                      onClick={() => {
                        if (!selectedEmail) return;
                        setManualSubject(selectedEmail.subject || '');
                        setManualSender(selectedEmail.sender || '');
                        setEmailInput(selectedEmail.body || '');
                      }}
                      disabled={!selectedEmail}
                    >
                      Copy to manual
                    </button>
                    <button className="soc-btn-primary" onClick={() => handleAnalyze(selectedEmail)} disabled={loading || !selectedEmail}>
                      {loading ? 'Analyzing...' : 'Analyze selected'}
                    </button>
                  </div>
                </div>

                <div className="mt-5 grid gap-4 lg:grid-cols-[0.72fr,1.28fr]">
                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Sender</p>
                    <p className="mt-2 text-sm text-white">{selectedEmail?.sender || 'Unavailable'}</p>
                    <p className="mt-4 text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Subject</p>
                    <p className="mt-2 text-sm text-white">{selectedEmail?.subject || 'Unavailable'}</p>
                  </div>
                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Body</p>
                    <p className="mt-2 text-sm leading-7 soc-text-muted">{selectedEmail?.body || 'Select an email from the inbox to inspect its contents.'}</p>
                  </div>
                </div>
              </section>
            </section>
          </div>
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}

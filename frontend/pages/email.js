import Link from 'next/link';
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import EmailHistoryTable from '../components/soc/EmailHistoryTable';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { analyzeEmail, clearEmailHistory, getEmailHistory, getInboxEmails } from '../services/api/email.service';

function mapHistory(items = []) {
  return [...items].reverse().map((entry, index) => ({
    id: `${entry.time || 'history'}-${index}`,
    subject: entry.input || 'Analyzed email',
    bodySnippet: entry.input || '',
    risk: entry.risk_score,
    severity: entry.severity,
    actions: entry.actions || [],
    time: entry.time || 'Unknown'
  }));
}

export default function EmailPage() {
  const [emails, setEmails] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [emailInput, setEmailInput] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchEmails = async () => {
    try {
      const inbox = await getInboxEmails();
      setEmails(inbox);
      setSelectedEmail((current) => current || inbox[0] || null);
    } catch (err) {
      setError(err.message || 'Unable to load inbox.');
    }
  };

  const fetchHistory = async () => {
    try {
      const entries = await getEmailHistory();
      setHistory(mapHistory(entries));
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
      const nextResult = await analyzeEmail(emailRecord.body);
      setResult(nextResult);
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
      const nextResult = await analyzeEmail(emailInput);
      setResult(nextResult);
      setEmailInput('');
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
                  <StatusBadge tone="medium">Risk {Number(result.risk_score || 0).toFixed(2)}</StatusBadge>
                </div>
                <div className="mt-5 grid gap-4 lg:grid-cols-[0.8fr,1.2fr]">
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
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Actions taken</p>
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
                  <button className="soc-btn-primary" onClick={() => handleAnalyze(selectedEmail)} disabled={loading || !selectedEmail}>
                    {loading ? 'Analyzing...' : 'Analyze selected'}
                  </button>
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

import Link from 'next/link';
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import EmailHistoryTable from '../components/soc/EmailHistoryTable';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { analyzeEmail, clearEmailHistory, getEmailHistory } from '../services/api/email.service';

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
  const [email, setEmail] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchHistory = async () => {
    try {
      const entries = await getEmailHistory();
      setHistory(mapHistory(entries));
    } catch (err) {
      setError(err.message || 'Unable to load email history.');
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleAnalyze = async () => {
    if (!email.trim()) {
      setError('Paste an email before running analysis.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const nextResult = await analyzeEmail(email);
      setResult(nextResult);
      setEmail('');
      await fetchHistory();
    } catch (err) {
      setError(err.message || 'Unable to analyze email.');
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
            description="Submit suspicious emails for scoring, review response actions, and monitor persistent history like a SOC investigation queue."
            actions={<Link href="/overview" className="soc-btn-secondary">Back to overview</Link>}
          />

          <div className="space-y-6">
            <section className="soc-panel">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="soc-kicker">Input</p>
                  <h2 className="mt-2 text-base font-semibold text-white">Paste email content</h2>
                </div>
                <button className="soc-btn-primary" onClick={handleAnalyze} disabled={loading}>
                  {loading ? 'Analyzing...' : 'Analyze email'}
                </button>
              </div>

              <textarea
                className="mt-5 min-h-[180px] w-full rounded-2xl border border-[rgba(65,71,85,0.45)] bg-[rgba(16,20,26,0.86)] px-4 py-4 text-sm leading-6 text-white outline-none transition focus:border-[#4b8eff]"
                placeholder="Paste suspicious email content here..."
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />

              {error ? <p className="mt-3 text-sm text-[#ffb3ad]">{error}</p> : null}
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
          </div>
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}

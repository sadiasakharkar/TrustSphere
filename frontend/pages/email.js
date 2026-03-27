import { useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { analyzeEmail } from '../services/api/email.service';

function humanSummary(result) {
  const severity = result?.severity || 'Medium';
  if (severity === 'HIGH') {
    return {
      happened: 'The system found signs that this message may be dangerous.',
      risky: 'The message looks unusual and could try to trick someone into clicking, opening, or sharing something unsafe.',
      action: 'Do not trust the message yet. Review it carefully and isolate it if needed.'
    };
  }
  if (severity === 'LOW') {
    return {
      happened: 'The system found only a small amount of unusual behavior.',
      risky: 'There are minor warning signs, but the overall risk is lower.',
      action: 'Keep monitoring it, but urgent action is not required right now.'
    };
  }
  return {
    happened: 'The system found some unusual behavior in the submitted data.',
    risky: 'There are enough warning signs to review it before treating it as safe.',
    action: 'Review the result and decide whether follow-up action is needed.'
  };
}

export default function EmailPage() {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleAnalyze = async () => {
    if (!input.trim()) {
      setError('Enter some sample data before running analysis.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const nextResult = await analyzeEmail(input, {
        subject: 'Demo input',
        sender: 'demo@trustsphere.local',
      });
      setResult(nextResult);
    } catch (err) {
      setError(err.message || 'Unable to run analysis right now.');
    } finally {
      setLoading(false);
    }
  };

  const summary = result ? humanSummary(result) : null;

  return (
    <RequireAuth>
      <Layout>
        <PageContainer>
          <PageHeader
            kicker="TrustSphere"
            title="Data Input"
            description="Paste a message or suspicious text below, then run a simple demo analysis."
          />

          <section className="grid gap-6 xl:grid-cols-[1.05fr,0.95fr]">
            <div className="soc-panel">
              <p className="soc-kicker">Input</p>
              <h2 className="mt-2 text-lg font-semibold text-white">Run demo analysis</h2>
              <p className="mt-2 text-sm leading-6 soc-text-muted">
                This page is intentionally simple. Paste sample content and click the button to see the AI result.
              </p>

              <textarea
                className="mt-5 min-h-[220px] w-full rounded-2xl border border-[rgba(65,71,85,0.45)] bg-[rgba(16,20,26,0.86)] px-4 py-4 text-sm leading-7 text-white outline-none transition focus:border-[#4b8eff]"
                placeholder="Example: An urgent email asking for login details or a suspicious payment request."
                value={input}
                onChange={(event) => setInput(event.target.value)}
              />

              {error ? <p className="mt-4 text-sm text-[#ffb3ad]">{error}</p> : null}

              <div className="mt-5">
                <button type="button" className="soc-btn-primary" onClick={handleAnalyze} disabled={loading}>
                  {loading ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>
            </div>

            <div className="soc-panel">
              <p className="soc-kicker">Result</p>
              <h2 className="mt-2 text-lg font-semibold text-white">AI detection result</h2>

              {!result ? (
                <p className="mt-4 text-sm leading-6 soc-text-muted">
                  No result yet. Run the analysis to see a clear explanation of what happened, why it is risky, and what to do next.
                </p>
              ) : (
                <div className="mt-4 space-y-4">
                  <div className="flex flex-wrap gap-2">
                    <StatusBadge tone={result.severity === 'HIGH' ? 'critical' : result.severity === 'LOW' ? 'low' : 'medium'}>
                      {result.severity}
                    </StatusBadge>
                    <StatusBadge tone="default">Risk {Number(result.risk_score || 0).toFixed(2)}</StatusBadge>
                  </div>

                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">What happened</p>
                    <p className="mt-2 text-sm leading-7 text-white">{summary?.happened}</p>
                  </div>

                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Why it is risky</p>
                    <p className="mt-2 text-sm leading-7 text-white">{summary?.risky}</p>
                  </div>

                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Suggested action</p>
                    <p className="mt-2 text-sm leading-7 text-white">{summary?.action}</p>
                  </div>
                </div>
              )}
            </div>
          </section>
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}

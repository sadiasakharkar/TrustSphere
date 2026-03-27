import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { useHybridData } from '../hooks/useHybridData';

function simpleAnalysis(incident) {
  if (!incident) {
    return {
      what: 'No incident has been selected yet.',
      why: 'There is not enough activity to explain a current risk.',
      action: 'Wait for a new alert or run a demo analysis.'
    };
  }

  return {
    what: incident.title || incident.eventType || 'TrustSphere detected unusual activity.',
    why: incident.evidence?.[0]?.content || 'The activity looks different from normal behavior and may indicate a security issue.',
    action: incident.evidence?.[2]?.content || 'Review the incident and take the suggested response step.'
  };
}

export default function AnalyticsPage() {
  const { data: incidents } = useHybridData('incidents', {}, { bootstrapDelayMs: 8000, pollIntervalMs: 6000 });
  const topIncident = incidents?.queue?.[0] || null;
  const summary = simpleAnalysis(topIncident);

  return (
    <RequireAuth>
      <Layout>
        <PageContainer>
          <SectionHeader
            eyebrow="TrustSphere"
            title="AI Analysis"
            description="A plain-language explanation of what the system saw, why it matters, and what to do next."
          />

          {!incidents ? <LoadingSkeleton rows={4} /> : (
            <section className="grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
              <div className="soc-panel">
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge tone={String(topIncident?.severity || '').toLowerCase().includes('high') || String(topIncident?.severity || '').toLowerCase().includes('critical') ? 'critical' : 'medium'}>
                    {topIncident?.severity || 'Medium'}
                  </StatusBadge>
                  <StatusBadge tone="default">{topIncident?.id || 'AI Summary'}</StatusBadge>
                </div>

                <div className="mt-6 space-y-4">
                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">What happened</p>
                    <p className="mt-2 text-sm leading-7 text-white">{summary.what}</p>
                  </div>
                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Why it is risky</p>
                    <p className="mt-2 text-sm leading-7 text-white">{summary.why}</p>
                  </div>
                  <div className="soc-panel-muted">
                    <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Suggested action</p>
                    <p className="mt-2 text-sm leading-7 text-white">{summary.action}</p>
                  </div>
                </div>
              </div>

              <div className="soc-panel">
                <p className="soc-kicker">Why this page is simple</p>
                <h2 className="mt-2 text-lg font-semibold text-white">Designed for quick understanding</h2>
                <ul className="mt-4 space-y-3 text-sm leading-6 soc-text-muted">
                  <li>The system explains the issue in normal language.</li>
                  <li>The risk is summarized without technical jargon.</li>
                  <li>The next action is clear and easy to follow.</li>
                </ul>
              </div>
            </section>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}

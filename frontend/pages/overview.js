import Link from 'next/link';
import { AnomalyLineChart } from '../components/Charts';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { useHybridData } from '../hooks/useHybridData';

function formatSeverity(level = '') {
  const normalized = String(level).toLowerCase();
  if (normalized.includes('critical') || normalized.includes('high')) return 'High';
  if (normalized.includes('medium')) return 'Medium';
  return 'Low';
}

function getSeverityTone(level = '') {
  const severity = formatSeverity(level);
  if (severity === 'High') return 'critical';
  if (severity === 'Medium') return 'medium';
  return 'low';
}

function toRiskSeries(values = []) {
  return Array.isArray(values) && values.length
    ? values.slice(0, 12)
    : [42, 48, 46, 52, 59, 57, 61, 67, 65, 72, 76, 74];
}

function toAnomalySeries(queue = []) {
  if (!Array.isArray(queue) || !queue.length) return [18, 22, 19, 24, 27, 30, 28, 34, 31, 36, 39, 37];
  return queue
    .slice(0, 12)
    .map((item, index) => Math.max(12, Math.round((Number(item.riskScore || item.risk_score || 40) * 0.45) - index)));
}

export default function OverviewPage() {
  const { data } = useHybridData('overview', {}, { bootstrapDelayMs: 8000, pollIntervalMs: 6000 });

  if (!data) {
    return (
      <RequireAuth>
        <Layout>
          <PageContainer>
            <LoadingSkeleton rows={6} />
          </PageContainer>
        </Layout>
      </RequireAuth>
    );
  }

  const topIncident = data.criticalQueue?.[0] || null;
  const riskScore = topIncident?.riskScore || topIncident?.risk_score || 74;
  const activeAlerts = data.criticalQueue?.length || 0;
  const severity = formatSeverity(topIncident?.severity);
  const severityTone = getSeverityTone(topIncident?.severity);

  return (
    <RequireAuth>
      <Layout>
        <PageContainer>
          <SectionHeader
            eyebrow="TrustSphere"
            title="Dashboard"
            description="A simple view of your security posture, designed to show what needs attention right now."
            actions={<Link href="/email" className="soc-btn-primary">Run demo analysis</Link>}
          />

          <section className="grid gap-4 md:grid-cols-3">
            <div className="soc-panel md:col-span-1">
              <p className="soc-kicker">Main Risk</p>
              <p className="mt-3 font-headline text-[56px] font-extrabold tracking-tight text-white">{riskScore}</p>
              <p className="mt-2 text-sm leading-6 soc-text-muted">
                This score highlights the most important threat currently detected by the platform.
              </p>
            </div>

            <div className="soc-panel-muted">
              <p className="soc-kicker">Active Alerts</p>
              <p className="mt-3 font-headline text-[42px] font-extrabold tracking-tight text-white">{activeAlerts}</p>
              <p className="mt-2 text-sm leading-6 soc-text-muted">Alerts that currently need review.</p>
            </div>

            <div className="soc-panel-muted">
              <p className="soc-kicker">Severity</p>
              <div className="mt-3">
                <StatusBadge tone={severityTone}>{severity}</StatusBadge>
              </div>
              <p className="mt-4 text-sm leading-6 soc-text-muted">How serious the most important issue is right now.</p>
            </div>
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-2">
            <AnomalyLineChart
              series={toRiskSeries(data.analytics?.riskDistribution)}
              title="Risk Trend"
              label="Risk score"
            />
            <AnomalyLineChart
              series={toAnomalySeries(data.criticalQueue)}
              title="Anomaly Trend"
              label="Anomaly level"
            />
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
            <div className="soc-panel">
              <SectionHeader
                eyebrow="Top Alert"
                title={topIncident?.title || 'No active alerts'}
                description="A short summary of the most important issue so anyone can understand it quickly."
              />
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">What happened</p>
                  <p className="mt-2 text-sm leading-6 text-white">
                    {topIncident?.eventType || topIncident?.title || 'TrustSphere found unusual activity that may need attention.'}
                  </p>
                </div>
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Suggested next step</p>
                  <p className="mt-2 text-sm leading-6 text-white">
                    Open the incident and review the recommended action before deciding how to respond.
                  </p>
                </div>
              </div>
            </div>

            <div className="soc-panel">
              <SectionHeader
                eyebrow="Quick Access"
                title="Go to the next step"
                description="Each page below gives one simple view of the current security situation."
              />
              <div className="mt-4 grid gap-3">
                <Link href="/monitoring" className="soc-btn-secondary">Open alerts</Link>
                <Link href="/analytics" className="soc-btn-secondary">Open AI analysis</Link>
                <Link href="/incidents" className="soc-btn-secondary">Open incidents</Link>
                <Link href="/email" className="soc-btn-primary">Open data input</Link>
              </div>
            </div>
          </section>
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}

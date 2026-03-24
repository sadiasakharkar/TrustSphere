import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import AIInsightPanel from '../components/soc/AIInsightPanel';
import AlertTable from '../components/soc/AlertTable';
import AuditBanner from '../components/soc/AuditBanner';
import IncidentCard from '../components/soc/IncidentCard';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import ModelHealthChip from '../components/soc/ModelHealthChip';
import PageHeader from '../components/soc/PageHeader';
import SeverityBadge from '../components/soc/SeverityBadge';
import { getOverviewSummary } from '../services/api/overviewService';

function MetricTile({ metric }) {
  return (
    <div className="soc-panel-muted">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[rgba(193,198,215,0.55)]">{metric.label}</p>
          <p className="mt-3 font-headline text-4xl font-extrabold tracking-tight text-white">{metric.value}</p>
        </div>
        <SeverityBadge level={metric.status}>{metric.status}</SeverityBadge>
      </div>
      <div className="mt-4 flex items-center justify-between gap-3 text-xs">
        <span className="font-semibold text-[rgba(223,226,235,0.86)]">{metric.delta}</span>
        <span className="soc-text-muted">{metric.helper}</span>
      </div>
    </div>
  );
}

export default function OverviewPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    getOverviewSummary().then((result) => {
      if (!mounted) return;
      setData(result);
      setLoading(false);
    });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <RequireAuth>
      <Layout insightSummary={{ title: 'Overview focus: monitor risk concentration, queue pressure, and model reliability before moving into triage.' }}>
        <PageHeader
          kicker="SOC Command"
          title="Enterprise SOC Overview"
          description="This workspace tracks operational posture across incident volume, anomaly concentration, attack-chain reconstruction, and AI copilot readiness. Analysts should start here before entering queue triage."
          actions={
            <>
              <button className="soc-btn-secondary"><span className="material-symbols-outlined text-base">filter_list</span>Filter scope</button>
              <button className="soc-btn-primary"><span className="material-symbols-outlined text-base">bolt</span>Start investigation</button>
            </>
          }
        />

        <AuditBanner title="Air-gapped enterprise mode active" description="All model inference, attack graph reconstruction, and SOC reasoning are executing locally against validated contracts." />

        {loading || !data ? (
          <div className="mt-6"><LoadingSkeleton rows={6} /></div>
        ) : (
          <div className="mt-6 space-y-6">
            <section className="grid gap-4 xl:grid-cols-4">
              {data.metrics.map((metric) => <MetricTile key={metric.label} metric={metric} />)}
            </section>

            <section className="grid gap-6 xl:grid-cols-[1.5fr,1fr]">
              <div className="soc-panel">
                <div className="mb-5 flex items-center justify-between gap-3">
                  <div>
                    <p className="soc-kicker">Triage pressure</p>
                    <h2 className="soc-section-title mt-2">Critical incident queue</h2>
                  </div>
                  <SeverityBadge level="critical">Needs response</SeverityBadge>
                </div>
                <div className="grid gap-4 lg:grid-cols-2">
                  {data.criticalQueue.map((incident) => <IncidentCard key={incident.id} incident={incident} />)}
                </div>
              </div>

              <AIInsightPanel
                title="SOC Analyst Summary"
                footer={<button className="soc-btn-secondary w-full">Open narrative briefing</button>}
              >
                <p>TrustSphere is observing a concentration of privileged-user anomalies around payroll and transfer processing segments.</p>
                <p>Attack-graph severity increased in the last 30 minutes due to correlated credential misuse and exfiltration telemetry.</p>
                <p>The recommended workflow is: review queue owners, validate chain scope, then move to containment playbooks.</p>
              </AIInsightPanel>
            </section>

            <section className="grid gap-6 xl:grid-cols-[1.2fr,0.8fr]">
              <div className="soc-panel">
                <div className="mb-5 flex items-center justify-between gap-3">
                  <div>
                    <p className="soc-kicker">Operational feed</p>
                    <h2 className="soc-section-title mt-2">Latest critical signals</h2>
                  </div>
                  <span className="text-xs soc-text-muted">Updated {new Date(data.generatedAt).toLocaleTimeString()}</span>
                </div>
                <AlertTable rows={data.criticalQueue.map((item) => ({ ...item, source: item.status, score: item.riskScore }))} compact />
              </div>
              <div className="soc-panel">
                <p className="soc-kicker">Model status</p>
                <h2 className="soc-section-title mt-2">Core intelligence health</h2>
                <div className="mt-5 space-y-3">
                  {data.modelHealth.map((item) => <ModelHealthChip key={item.name} {...item} />)}
                </div>
              </div>
            </section>

            <section className="soc-panel">
              <div className="mb-5 flex items-center justify-between gap-3">
                <div>
                  <p className="soc-kicker">Unified pipeline</p>
                  <h2 className="soc-section-title mt-2">Detection and reasoning stages</h2>
                </div>
                <SeverityBadge level="healthy">All stages reporting</SeverityBadge>
              </div>
              <div className="grid gap-3 md:grid-cols-2 2xl:grid-cols-4">
                {data.pipeline.map((item) => (
                  <div key={item.module} className="soc-panel-muted">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-semibold text-white">{item.module}</p>
                      <SeverityBadge level={item.status}>{item.status}</SeverityBadge>
                    </div>
                    <p className="mt-3 text-sm leading-6 soc-text-muted">{item.detail}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}
      </Layout>
    </RequireAuth>
  );
}

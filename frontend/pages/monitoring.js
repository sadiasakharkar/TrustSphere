import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { useHybridData } from '../hooks/useHybridData';

function severityTone(value = '') {
  const normalized = String(value).toLowerCase();
  if (normalized.includes('critical') || normalized.includes('high')) return 'critical';
  if (normalized.includes('medium')) return 'medium';
  return 'low';
}

export default function MonitoringPage() {
  const { data } = useHybridData('monitoring', {}, { bootstrapDelayMs: 8000, pollIntervalMs: 6000 });

  return (
    <RequireAuth>
      <Layout>
        <PageContainer>
          <SectionHeader
            eyebrow="TrustSphere"
            title="Alerts"
            description="A simple list of alerts showing only severity, time, and a short message."
          />

          {!data ? <LoadingSkeleton rows={5} /> : (
            <section className="space-y-4">
              {(data.events || []).map((alert) => (
                <article key={alert.id} className="soc-panel">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="text-base font-semibold text-white">{alert.eventType}</p>
                      <p className="mt-2 text-sm leading-6 soc-text-muted">
                        {alert.entity} showed unusual activity and was flagged for review.
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge tone={severityTone(alert.severity)}>{alert.severity}</StatusBadge>
                      <StatusBadge tone="default">{alert.timestamp}</StatusBadge>
                    </div>
                  </div>
                </article>
              ))}
            </section>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}

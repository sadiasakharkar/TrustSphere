import DashboardLayout from '../components/dashboard/DashboardLayout';
import RequireAuth from '../components/RequireAuth';
import MetricCard from '../components/soc/MetricCard';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { useHybridData } from '../hooks/useHybridData';

function getTone(value) {
  const normalized = String(value || '').toLowerCase();
  if (normalized.includes('critical')) return 'critical';
  if (normalized.includes('high')) return 'high';
  if (normalized.includes('healthy') || normalized.includes('ready')) return 'healthy';
  return 'medium';
}

export default function OverviewPage() {
  const { session } = useAuth();
  const { data } = useHybridData('overview');
  const metrics = Array.isArray(data?.metrics) ? data.metrics : [];
  const queue = Array.isArray(data?.criticalQueue) ? data.criticalQueue.slice(0, 4) : [];
  const modelHealth = Array.isArray(data?.modelHealth) ? data.modelHealth : [];

  return (
    <RequireAuth>
      <DashboardLayout role={session.role}>
        <PageContainer>
          <PageHeader kicker="SOC" title="Overview" />

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {metrics.map((metric, index) => (
              <MetricCard
                key={`${metric.label || metric.title}-${index}`}
                label={metric.label || metric.title || 'Metric'}
                value={metric.value || '--'}
                delta={metric.delta || data?.sourceMode || 'live'}
                tone={getTone(metric.delta || metric.label)}
              />
            ))}
          </div>

          <div className="grid gap-4 lg:grid-cols-[1.25fr_0.95fr]">
            <section className="soc-panel">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <p className="soc-kicker">Queue</p>
                  <h2 className="soc-section-title">Priority</h2>
                </div>
                <StatusBadge tone={data?.sourceMode === 'live' ? 'healthy' : 'medium'}>{data?.sourceMode || 'demo'}</StatusBadge>
              </div>
              <div className="grid gap-3">
                {queue.map((incident) => (
                  <div key={incident.id} className="soc-panel-muted flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-white">{incident.title}</p>
                      <p className="mt-1 text-xs soc-text-muted">{incident.entities?.[0] || incident.entity}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusBadge tone={incident.severity}>{incident.severity}</StatusBadge>
                      <span className="text-sm font-semibold text-white">{incident.risk_score || incident.riskScore}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="soc-panel">
              <p className="soc-kicker">Systems</p>
              <h2 className="soc-section-title">Health</h2>
              <div className="mt-4 grid gap-3">
                {modelHealth.map((model) => (
                  <div key={model.name} className="soc-panel-muted flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-white">{model.name}</p>
                    <StatusBadge tone={getTone(model.status)}>{model.status}</StatusBadge>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </PageContainer>
      </DashboardLayout>
    </RequireAuth>
  );
}

import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { useHybridData } from '../hooks/useHybridData';

function toneForSeverity(level = '') {
  const normalized = String(level).toLowerCase();
  if (normalized.includes('critical') || normalized.includes('high')) return 'critical';
  if (normalized.includes('medium')) return 'medium';
  return 'low';
}

function toneForStatus(status = '') {
  const normalized = String(status).toLowerCase();
  if (normalized.includes('resolved')) return 'resolved';
  return 'open';
}

export default function IncidentsPage() {
  const { data } = useHybridData('incidents', {}, { bootstrapDelayMs: 8000, pollIntervalMs: 6000 });
  const queue = data?.queue || [];

  return (
    <RequireAuth>
      <Layout>
        <PageContainer>
          <SectionHeader
            eyebrow="TrustSphere"
            title="Incidents"
            description="A simple list of incidents showing status, severity, and a short description."
          />

          {!data ? <LoadingSkeleton rows={5} /> : (
            <div className="soc-panel overflow-hidden">
              <div className="overflow-x-auto">
                <table className="soc-table">
                  <thead>
                    <tr>
                      <th>Status</th>
                      <th>Severity</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {queue.map((incident) => (
                      <tr key={incident.id} className="soc-table-row">
                        <td>
                          <StatusBadge tone={toneForStatus(incident.status)}>{incident.status}</StatusBadge>
                        </td>
                        <td>
                          <StatusBadge tone={toneForSeverity(incident.severity)}>{incident.severity}</StatusBadge>
                        </td>
                        <td>
                          <p className="font-medium text-white">{incident.title || incident.eventType}</p>
                          <p className="mt-1 text-sm soc-text-muted">{incident.entity}</p>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}

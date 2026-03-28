import DashboardLayout from '../components/dashboard/DashboardLayout';
import DataTable from '../components/soc/DataTable';
import MetricCard from '../components/soc/MetricCard';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import RequireAuth from '../components/RequireAuth';
import { useAuth } from '../context/AuthContext';
import { useHybridData } from '../hooks/useHybridData';

export default function AnalyticsPage() {
  const { session } = useAuth();
  const { data } = useHybridData('analytics');
  const labels = Array.isArray(data?.severityLabels) ? data.severityLabels : [];
  const values = Array.isArray(data?.severityValues) ? data.severityValues : [];
  const rows = Array.isArray(data?.recentActivity) ? data.recentActivity : [];

  return (
    <RequireAuth>
      <DashboardLayout role={session.role}>
        <PageContainer>
          <PageHeader kicker="UEBA" title="Analytics" />

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {labels.map((label, index) => (
              <MetricCard
                key={label}
                label={label}
                value={values[index] ?? '--'}
                delta="trend"
                tone={String(label).toLowerCase()}
                role={session.role}
              />
            ))}
          </div>

          <section className="soc-panel">
            <p className="soc-kicker">Activity</p>
            <h2 className="soc-section-title">Anomalies</h2>
            <div className="mt-4">
              <DataTable
                columns={[
                  { key: 'entity', label: 'Entity' },
                  { key: 'eventType', label: 'Signal' },
                  { key: 'severity', label: 'Severity' },
                  { key: 'score', label: 'Score' },
                ]}
                rows={rows}
                getRowKey={(row) => row.id}
                renderCell={(row, key) => <span className="text-sm text-white">{row[key] ?? '--'}</span>}
              />
            </div>
          </section>
        </PageContainer>
      </DashboardLayout>
    </RequireAuth>
  );
}

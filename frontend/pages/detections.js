import Link from 'next/link';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import DataTable from '../components/soc/DataTable';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import RequireAuth from '../components/RequireAuth';
import StatusBadge from '../components/soc/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { useHybridData } from '../hooks/useHybridData';

const columns = [
  { key: 'source', label: 'Source' },
  { key: 'status', label: 'Status' },
  { key: 'precision', label: 'Precision' },
  { key: 'drift', label: 'Drift' },
  { key: 'action', label: 'Action' },
];

export default function DetectionsPage() {
  const { session } = useAuth();
  const { data } = useHybridData('detections');
  const detectors = Array.isArray(data?.detectors) ? data.detectors : [];

  return (
    <RequireAuth>
      <DashboardLayout role={session.role}>
        <PageContainer>
          <PageHeader kicker="Detections" title="Detections" />

          <section className="soc-panel">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="soc-kicker">Email</p>
                <h2 className="soc-section-title">Analysis</h2>
              </div>
              <StatusBadge tone="medium">{data?.sourceMode || 'demo'}</StatusBadge>
            </div>
            <DataTable
              columns={columns}
              rows={detectors}
              getRowKey={(row) => row.id || row.source}
              renderCell={(row, key) => {
                if (key === 'status') return <StatusBadge tone={String(row.status).includes('High') ? 'high' : 'healthy'}>{row.status}</StatusBadge>;
                if (key === 'precision') return <span className="text-sm text-white">{row.precision ?? '--'}</span>;
                if (key === 'drift') return <span className="text-sm text-white">{row.drift || '--'}</span>;
                if (key === 'action') {
                  return (
                    <Link href={`/incidents?create=${encodeURIComponent(row.id || row.source)}`} className="soc-btn-secondary">
                      Create Incident
                    </Link>
                  );
                }
                return <span className="text-sm text-white">{row[key] || '--'}</span>;
              }}
              renderExpandedRow={(row) => (
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="soc-panel-muted">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">Detector</p>
                    <p className="mt-2 text-sm font-semibold text-white">{row.source}</p>
                  </div>
                  <div className="soc-panel-muted">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] soc-text-muted">Signal</p>
                    <p className="mt-2 text-sm font-semibold text-white">{row.status}</p>
                  </div>
                </div>
              )}
            />
          </section>
        </PageContainer>
      </DashboardLayout>
    </RequireAuth>
  );
}

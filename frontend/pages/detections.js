import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import DataTable from '../components/soc/DataTable';
import EmptyState from '../components/soc/EmptyState';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { getDetectionsOverview } from '../services/api/detectionService';

const columns = [
  { key: 'source', label: 'Detector' },
  { key: 'version', label: 'Version' },
  { key: 'precision', label: 'Precision' },
  { key: 'drift', label: 'Drift' },
  { key: 'status', label: 'Status' }
];

export default function DetectionsPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const response = await getDetectionsOverview();
        if (active) setData(response);
      } catch (err) {
        if (active) setError(err.message || 'Unable to load detections.');
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <RequireAuth adminOnly>
      <Layout>
        <PageContainer>
          <SectionHeader eyebrow="Detections" title="Detector Health" description="Administrative detector posture and model health for the current SOC environment." />
          {!data && !error ? <LoadingSkeleton rows={5} /> : error ? <EmptyState title="Detector health snapshot" detail={error} /> : (
            <section className="soc-panel">
              <DataTable
                columns={columns}
                rows={data.detectors || []}
                getRowKey={(row) => row.id || row.source}
                renderCell={(row, key) => {
                  if (key === 'status') return <StatusBadge tone={row.status}>{row.status}</StatusBadge>;
                  return row[key];
                }}
              />
            </section>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}

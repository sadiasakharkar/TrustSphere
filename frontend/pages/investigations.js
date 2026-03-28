import Link from 'next/link';
import { useRouter } from 'next/router';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import DataTable from '../components/soc/DataTable';
import GraphPanel from '../components/soc/GraphPanel';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import RequireAuth from '../components/RequireAuth';
import { useAuth } from '../context/AuthContext';
import { useHybridData } from '../hooks/useHybridData';

const entityColumns = [
  { key: 'entity', label: 'Entity' },
  { key: 'type', label: 'Type' },
  { key: 'score', label: 'Score' },
  { key: 'events', label: 'Events' },
];

export default function InvestigationsPage() {
  const router = useRouter();
  const { session } = useAuth();
  const incidentId = typeof router.query.incident === 'string' ? router.query.incident : undefined;
  const { data: workspace } = useHybridData('investigations');
  const { data: graph } = useHybridData('attackGraph', { id: incidentId });
  const entities = Array.isArray(workspace?.entities) ? workspace.entities : [];
  const relatedEvidence = Array.isArray(workspace?.relatedEvidence) ? workspace.relatedEvidence : [];

  return (
    <RequireAuth>
      <DashboardLayout role={session.role}>
        <PageContainer>
          <PageHeader kicker="Investigation" title="Investigations" />

          <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
            <GraphPanel graph={graph || { nodes: [], edges: [], chains: [] }} />

            <section className="soc-panel">
              <p className="soc-kicker">Correlations</p>
              <h2 className="soc-section-title">Entities</h2>
              <div className="mt-4">
                <DataTable
                  columns={entityColumns}
                  rows={entities}
                  getRowKey={(row) => row.entity}
                  renderCell={(row, key) => <span className="text-sm text-white">{row[key] ?? '--'}</span>}
                  renderExpandedRow={(row) => (
                    <div className="flex flex-wrap gap-2">
                      <Link href={`/incidents?entity=${encodeURIComponent(row.entity)}`} className="soc-btn-secondary">Related Incidents</Link>
                    </div>
                  )}
                />
              </div>
            </section>
          </div>

          <section className="soc-panel">
            <p className="soc-kicker">Evidence</p>
            <h2 className="soc-section-title">Signals</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {relatedEvidence.map((item, index) => (
                <div key={`${item.value}-${index}`} className="soc-panel-muted">
                  <p className="text-sm font-semibold text-white">{item.value}</p>
                  <p className="mt-2 text-sm soc-text-muted">{item.note}</p>
                </div>
              ))}
            </div>
          </section>
        </PageContainer>
      </DashboardLayout>
    </RequireAuth>
  );
}

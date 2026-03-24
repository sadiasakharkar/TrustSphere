import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import EmptyState from '../components/soc/EmptyState';
import EntityPill from '../components/soc/EntityPill';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageHeader from '../components/soc/PageHeader';
import { getInvestigationWorkspace } from '../services/api/detectionService';

export default function InvestigationsPage() {
  const [data, setData] = useState(null);
  useEffect(() => { getInvestigationWorkspace().then(setData); }, []);

  return (
    <RequireAuth>
      <Layout insightSummary={{ title: 'Investigation focus: pivot across users, hosts, IPs, and evidence fragments to validate compromise scope.' }}>
        <PageHeader kicker="Investigations" title="Evidence Workspace" description="Use this view to inspect anomalous entities, connected evidence, and correlated observables before formal response action is approved." />
        {!data ? <LoadingSkeleton rows={4} /> : !data.entities.length ? <EmptyState /> : (
          <div className="grid gap-6 xl:grid-cols-[1fr,1fr]">
            <section className="soc-panel">
              <h2 className="soc-section-title">Top anomalous entities</h2>
              <div className="mt-5 space-y-3">
                {data.entities.map((entity) => (
                  <div key={entity.entity} className="soc-panel-muted">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{entity.entity}</p>
                        <p className="mt-1 text-xs soc-text-muted">{entity.signal}</p>
                      </div>
                      <EntityPill label={`${entity.score}`} type={entity.type} />
                    </div>
                  </div>
                ))}
              </div>
            </section>
            <section className="soc-panel">
              <h2 className="soc-section-title">Linked evidence</h2>
              <div className="mt-5 space-y-3">
                {data.relatedEvidence.map((evidence) => (
                  <div key={evidence.id} className="soc-panel-muted">
                    <p className="text-sm font-semibold text-white">{evidence.value}</p>
                    <p className="mt-1 text-xs soc-text-muted">{evidence.type}</p>
                    <p className="mt-3 text-sm leading-6 soc-text-muted">{evidence.note}</p>
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

import Link from 'next/link';
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import GraphPanel from '../components/soc/GraphPanel';
import EmptyState from '../components/soc/EmptyState';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { getThreatGraph } from '../services/api/graphService';
import { getWorkflowInsight } from '../services/api/insight.service';

export default function ThreatGraphPage() {
  const [data, setData] = useState(null);
  const [insight, setInsight] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const graph = await getThreatGraph();
        if (active) {
          setData(graph);
          const workflow = await getWorkflowInsight('threat-graph');
          if (active) setInsight(workflow);
        }
      } catch (err) {
        if (active) setError(err.message || 'Unable to load attack graph.');
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <RequireAuth>
      <Layout insightSummary={insight}>
        <PageContainer>
          <SectionHeader
            eyebrow="Attack Graph"
            title="Attack Path Visualization"
            description="Trace attacker movement through a centered graph view and validate chain severity using the supporting context panel."
            actions={<Link href="/playbooks" className="soc-btn-primary">Continue to response</Link>}
          />

          {!data && !error ? <LoadingSkeleton rows={5} /> : error ? <EmptyState title="Attack graph unavailable" detail={error} /> : (
            <div className="grid gap-6 xl:grid-cols-[1.35fr,0.65fr]">
              <div className="soc-panel">
                <GraphPanel graph={data} />
              </div>
              <div className="space-y-4">
                <div className="soc-panel">
                  <SectionHeader eyebrow="Chains" title="Linked sequences" />
                  <div className="mt-4 space-y-3">
                    {data.chains.map((chain) => (
                      <div key={chain.id} className="soc-panel-muted">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-white">{chain.title}</p>
                            <p className="mt-1 text-xs soc-text-muted">{chain.id} · confidence {chain.confidence}</p>
                          </div>
                          <StatusBadge tone={chain.severity}>{chain.severity}</StatusBadge>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}

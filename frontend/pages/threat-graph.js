import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
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
  const hasLoadedRef = useRef(false);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const graph = await getThreatGraph();
        if (active) {
          setData(graph);
          hasLoadedRef.current = true;
          setError('');
          const workflow = await getWorkflowInsight('threat-graph');
          if (active) setInsight(workflow);
        }
      } catch (err) {
        if (active && !hasLoadedRef.current) setError(err.message || 'Unable to load attack graph.');
      }
    };
    load();
    const interval = window.setInterval(load, 2000);
    return () => {
      active = false;
      window.clearInterval(interval);
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

          {!data && !error ? <LoadingSkeleton rows={5} /> : error ? <EmptyState title="Offline attack graph snapshot" detail={error} /> : (
            <div className="space-y-6">
              <section className="grid gap-4 md:grid-cols-3">
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Nodes</p>
                  <p className="mt-3 font-headline text-[32px] font-extrabold tracking-tight text-white">{data.nodes?.length || 0}</p>
                </div>
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Edges</p>
                  <p className="mt-3 font-headline text-[32px] font-extrabold tracking-tight text-white">{data.edges?.length || 0}</p>
                </div>
                <div className="soc-panel-muted">
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[rgba(193,198,215,0.58)]">Chains</p>
                  <p className="mt-3 font-headline text-[32px] font-extrabold tracking-tight text-white">{data.chains?.length || 0}</p>
                </div>
              </section>

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
                <div className="soc-panel">
                  <SectionHeader eyebrow="Nodes" title="High-risk entities" />
                  <div className="mt-4 space-y-3">
                    {(data.nodes || []).slice(0, 5).map((node) => (
                      <div key={node.id} className="soc-panel-muted flex items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-white">{node.label}</p>
                          <p className="mt-1 text-xs soc-text-muted">{node.type}</p>
                        </div>
                        <StatusBadge tone={node.risk}>{node.risk}</StatusBadge>
                      </div>
                    ))}
                  </div>
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

import { useEffect, useState } from 'react';
import GraphPanel from '../components/soc/GraphPanel';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageHeader from '../components/soc/PageHeader';
import SeverityBadge from '../components/soc/SeverityBadge';
import { getThreatGraph } from '../services/api/graphService';

export default function ThreatGraphPage() {
  const [data, setData] = useState(null);
  useEffect(() => { getThreatGraph().then(setData); }, []);

  return (
    <RequireAuth>
      <Layout insightSummary={{ title: 'Threat graph focus: validate attacker movement, locate pivots, and measure chain severity before containment.' }}>
        <PageHeader kicker="Threat Graph" title="Correlated Attack Chains" description="The graph workspace reconstructs attacker progression across users, hosts, and IPs. Use it to validate scope and sequence before taking containment steps." />
        {!data ? <LoadingSkeleton rows={4} /> : (
          <div className="grid gap-6 xl:grid-cols-[1.35fr,0.65fr]">
            <GraphPanel graph={data} />
            <section className="soc-panel">
              <p className="soc-kicker">Detected chains</p>
              <h2 className="soc-section-title mt-2">Investigation-ready sequences</h2>
              <div className="mt-5 space-y-3">
                {data.chains.map((chain) => (
                  <div key={chain.id} className="soc-panel-muted">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{chain.title}</p>
                        <p className="mt-1 text-xs soc-text-muted">{chain.id} · confidence {chain.confidence}</p>
                      </div>
                      <SeverityBadge level={chain.severity}>{chain.severity}</SeverityBadge>
                    </div>
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

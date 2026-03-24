import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageHeader from '../components/soc/PageHeader';
import PlaybookChecklist from '../components/soc/PlaybookChecklist';
import { getResponseWorkspace } from '../services/api/detectionService';

export default function ResponsePage() {
  const [data, setData] = useState(null);
  useEffect(() => { getResponseWorkspace().then(setData); }, []);

  return (
    <RequireAuth>
      <Layout insightSummary={{ title: 'Response focus: follow AI-generated playbooks, log approval states, and document action progress for auditability.' }}>
        <PageHeader kicker="Response" title="Playbooks and Containment" description="Use generated response plans to coordinate containment, remediation, and escalation with clear owner assignments and execution tracking." />
        {!data ? <LoadingSkeleton rows={4} /> : (
          <div className="grid gap-6 xl:grid-cols-[1fr,0.9fr]">
            <section className="soc-panel">
              <h2 className="soc-section-title">Recommended playbook</h2>
              <div className="mt-5"><PlaybookChecklist steps={data.playbook} /></div>
            </section>
            <section className="soc-panel">
              <h2 className="soc-section-title">Approval states</h2>
              <div className="mt-5"><PlaybookChecklist steps={data.approvals} /></div>
            </section>
          </div>
        )}
      </Layout>
    </RequireAuth>
  );
}

import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import GraphPanel from '../../components/soc/GraphPanel';
import Layout from '../../components/Layout';
import RequireAuth from '../../components/RequireAuth';
import AIInsightPanel from '../../components/soc/AIInsightPanel';
import EntityPill from '../../components/soc/EntityPill';
import EvidenceAccordion from '../../components/soc/EvidenceAccordion';
import LoadingSkeleton from '../../components/soc/LoadingSkeleton';
import PageHeader from '../../components/soc/PageHeader';
import PlaybookChecklist from '../../components/soc/PlaybookChecklist';
import SeverityBadge from '../../components/soc/SeverityBadge';
import TimelineRail from '../../components/soc/TimelineRail';
import { graphWorkspace } from '../../data/socConsoleData';
import { getIncidentDetail } from '../../services/api/incidentService';

export default function IncidentDetailPage() {
  const router = useRouter();
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!router.query.id) return;
    getIncidentDetail(router.query.id).then(setData);
  }, [router.query.id]);

  return (
    <RequireAuth>
      <Layout insightSummary={{ title: 'Incident detail focus: validate timeline, evidence, affected entities, and graph sequence before response approval.' }}>
        {!data ? <LoadingSkeleton rows={6} /> : (
          <div className="space-y-6">
            <PageHeader kicker="Incident Detail" title={data.summary.title} description="This incident workspace consolidates UEBA, graph, and reasoning context so analysts can move from triage into evidence-backed response." actions={<SeverityBadge level={data.summary.severity}>{data.summary.severity}</SeverityBadge>} />
            <section className="grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
              <div className="soc-panel">
                <div className="flex flex-wrap items-center gap-3">
                  <EntityPill type="Owner" label={data.summary.owner} />
                  <EntityPill type="Confidence" label={data.summary.confidence} />
                  <EntityPill type="Status" label={data.summary.status} />
                </div>
                <div className="mt-5 flex flex-wrap gap-2">
                  {data.summary.users.map((user) => <EntityPill key={user} type="User" label={user} />)}
                  {data.summary.hosts.map((host) => <EntityPill key={host} type="Host" label={host} />)}
                </div>
                <div className="mt-6">
                  <h2 className="soc-section-title">Incident timeline</h2>
                  <div className="mt-5"><TimelineRail items={data.timeline} /></div>
                </div>
              </div>
              <AIInsightPanel title="Narrative intelligence" footer={<div className="flex gap-3"><button className="soc-btn-secondary flex-1">Escalate</button><button className="soc-btn-primary flex-1">Resolve</button></div>}>
                <p>Credential compromise is the most likely initiating cause based on impossible-travel login, failed attempts, and follow-on privileged token use.</p>
                <p>Business impact is concentrated around payroll and identity infrastructure, with elevated exfiltration risk if containment is delayed.</p>
                <p>MITRE coverage: {data.summary.mitre.join(' · ')}</p>
              </AIInsightPanel>
            </section>
            <section className="grid gap-6 xl:grid-cols-[0.95fr,1.05fr]">
              <section className="soc-panel">
                <h2 className="soc-section-title">Evidence stack</h2>
                <div className="mt-5"><EvidenceAccordion items={data.evidence} /></div>
                <h3 className="mt-6 text-base font-semibold text-white">Suggested playbook</h3>
                <div className="mt-4"><PlaybookChecklist steps={[{ title: 'Contain privileged access', detail: 'Disable service tokens and isolate lateral movement path.', owner: 'IAM + IR', confidence: 94 }, { title: 'Block exfiltration route', detail: 'Terminate destination sessions and block outbound route at perimeter.', owner: 'Network Ops', confidence: 92 }]} /></div>
              </section>
              <GraphPanel graph={graphWorkspace} />
            </section>
          </div>
        )}
      </Layout>
    </RequireAuth>
  );
}

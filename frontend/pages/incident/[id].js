import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import GraphPanel from '../../components/soc/GraphPanel';
import Layout from '../../components/Layout';
import RequireAuth from '../../components/RequireAuth';
import AIInsightPanel from '../../components/soc/AIInsightPanel';
import EntityPill from '../../components/soc/EntityPill';
import EvidenceAccordion from '../../components/soc/EvidenceAccordion';
import EmptyState from '../../components/soc/EmptyState';
import LoadingSkeleton from '../../components/soc/LoadingSkeleton';
import PageContainer from '../../components/soc/PageContainer';
import PageHeader from '../../components/soc/PageHeader';
import PlaybookChecklist from '../../components/soc/PlaybookChecklist';
import SeverityBadge from '../../components/soc/SeverityBadge';
import TimelineRail from '../../components/soc/TimelineRail';
import { getIncidentDetail } from '../../services/api/incidentService';
import { getThreatGraph } from '../../services/api/graphService';
import { getPlaybooks } from '../../services/api/detectionService';

export default function IncidentDetailPage() {
  const router = useRouter();
  const [data, setData] = useState(null);
  const [graph, setGraph] = useState(null);
  const [playbooks, setPlaybooks] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!router.query.id) return;
    let active = true;
    (async () => {
      try {
        const [incident, incidentGraph, availablePlaybooks] = await Promise.all([
          getIncidentDetail(router.query.id),
          getThreatGraph(router.query.id),
          getPlaybooks()
        ]);
        if (!active) return;
        setData(incident);
        setGraph(incidentGraph);
        setPlaybooks(availablePlaybooks?.playbooks || []);
      } catch (err) {
        if (active) setError(err.message || 'Unable to load incident workspace.');
      }
    })();
    return () => {
      active = false;
    };
  }, [router.query.id]);

  return (
    <RequireAuth>
      <Layout
        insightSummary={{
          title: 'Incident detail focus',
          description: 'Validate timeline, evidence, affected entities, and graph sequence before approving containment or resolution.',
          bullets: [
            'Confirm initiating access signal before escalation.',
            'Check privileged asset exposure in the graph path.',
            'Use evidence stack to support response decisions.'
          ]
        }}
      >
        {!data && !error ? <LoadingSkeleton rows={6} /> : error ? <PageContainer><EmptyState title="Incident unavailable" detail={error} /></PageContainer> : (
          <PageContainer>
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
                <p>{data.evidence?.[0]?.content || 'Behavioral evidence is still being compiled.'}</p>
                <p>{data.evidence?.[2]?.content || 'Attack-path correlation summary is pending.'}</p>
                <p>MITRE coverage: {data.summary.mitre.join(' · ')}</p>
              </AIInsightPanel>
            </section>
            <section className="grid gap-6 xl:grid-cols-[0.95fr,1.05fr]">
              <section className="soc-panel">
                <h2 className="soc-section-title">Evidence stack</h2>
                <div className="mt-5"><EvidenceAccordion items={data.evidence} /></div>
                <h3 className="mt-6 text-base font-semibold text-white">Suggested playbook</h3>
                <div className="mt-4"><PlaybookChecklist steps={playbooks?.[0]?.steps || []} /></div>
              </section>
              <GraphPanel graph={graph || { nodes: [], edges: [], chains: [] }} />
            </section>
          </PageContainer>
        )}
      </Layout>
    </RequireAuth>
  );
}

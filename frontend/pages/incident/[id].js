import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useRef, useState } from 'react';
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
import { getIncidentInsight } from '../../services/api/insight.service';
import { useHybridData } from '../../hooks/useHybridData';

export default function IncidentDetailPage() {
  const router = useRouter();
  const [insight, setInsight] = useState(null);
  const incidentId = typeof router.query.id === 'string' ? router.query.id : '';
  const { data } = useHybridData('incidentDetail', { id: incidentId }, { enabled: Boolean(incidentId), bootstrapDelayMs: 8000, pollIntervalMs: 6000 });
  const { data: graph } = useHybridData('attackGraph', { id: incidentId }, { enabled: Boolean(incidentId), bootstrapDelayMs: 8000, pollIntervalMs: 6000 });
  const { data: playbookData } = useHybridData('playbooks', {}, { enabled: true, bootstrapDelayMs: 8000, pollIntervalMs: 6000 });
  const playbooks = playbookData?.playbooks || [];

  useEffect(() => {
    if (!incidentId) return;
    let active = true;
    const load = async () => {
      try {
        const summary = await getIncidentInsight(incidentId);
        if (active) setInsight(summary);
      } catch {
        if (active) setInsight(null);
      }
    };
    load();
    const interval = window.setInterval(load, 6000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [incidentId]);

  return (
    <RequireAuth>
      <Layout insightSummary={insight}>
        {!data ? <LoadingSkeleton rows={6} /> : (
          <PageContainer>
            <PageHeader
              kicker="Incident Detail"
              title={data.summary.title}
              description="This incident workspace consolidates UEBA, graph, and reasoning context so analysts can move from triage into evidence-backed response."
              actions={
                <div className="flex flex-wrap items-center gap-3">
                  <SeverityBadge level={data.summary.severity}>{data.summary.severity}</SeverityBadge>
                  <Link href="/investigations" className="soc-btn-secondary">Investigate</Link>
                  <Link href="/threat-graph" className="soc-btn-secondary">Attack graph</Link>
                  <Link href="/playbooks" className="soc-btn-primary">Run playbook</Link>
                </div>
              }
            />
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

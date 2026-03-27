import Link from 'next/link';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import Layout from '../../components/Layout';
import RequireAuth from '../../components/RequireAuth';
import AIInsightPanel from '../../components/soc/AIInsightPanel';
import ActionRecommendationPanel from '../../components/soc/ActionRecommendationPanel';
import EntityPill from '../../components/soc/EntityPill';
import EvidenceAccordion from '../../components/soc/EvidenceAccordion';
import GraphPanel from '../../components/soc/GraphPanel';
import LoadingSkeleton from '../../components/soc/LoadingSkeleton';
import PageContainer from '../../components/soc/PageContainer';
import PageHeader from '../../components/soc/PageHeader';
import PlaybookChecklist from '../../components/soc/PlaybookChecklist';
import SeverityBadge from '../../components/soc/SeverityBadge';
import StatusIndicator from '../../components/soc/StatusIndicator';
import TimelineRail from '../../components/soc/TimelineRail';
import { useRealtimeIncidents } from '../../hooks/useRealtimeIncidents';
import { useHybridData } from '../../hooks/useHybridData';
import { getIncidentInsight } from '../../services/api/insight.service';
import { assignIncident, updateIncidentStatus } from '../../services/api/incident.service';
import { runPlaybook } from '../../services/api/playbook.service';
import { deriveIncidentActionPlan, formatActionLabel } from '../../services/actionAdvisor';

function buildTimelineEntry(label, detail) {
  const now = new Date();
  return {
    time: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    title: label,
    detail
  };
}

export default function IncidentDetailPage() {
  const router = useRouter();
  const [insight, setInsight] = useState(null);
  const [lastStreamEvent, setLastStreamEvent] = useState(null);
  const [executingActionId, setExecutingActionId] = useState('');
  const [executionMessage, setExecutionMessage] = useState('');
  const [localIncident, setLocalIncident] = useState(null);
  const [toast, setToast] = useState(null);
  const incidentId = typeof router.query.id === 'string' ? router.query.id : '';
  const { data, status } = useHybridData('incidentDetail', { id: incidentId }, { enabled: Boolean(incidentId), bootstrapDelayMs: 8000, pollIntervalMs: 6000 });
  const { data: graph } = useHybridData('attackGraph', { id: incidentId }, { enabled: Boolean(incidentId), bootstrapDelayMs: 8000, pollIntervalMs: 6000 });
  const { data: playbookData } = useHybridData('playbooks', {}, { enabled: true, bootstrapDelayMs: 8000, pollIntervalMs: 6000 });
  const playbooks = playbookData?.playbooks || [];
  const incident = localIncident || data;
  const actionPlan = deriveIncidentActionPlan(incident, playbooks);

  useEffect(() => {
    setLocalIncident(data || null);
  }, [data]);

  useRealtimeIncidents({
    enabled: status.backendConnected,
    onEvent: (event) => {
      if (event?.payload?.incident_id === incidentId || event?.payload?.incident?.id === incidentId) {
        setLastStreamEvent(event);
        if (event?.payload?.incident) {
          setLocalIncident((current) => ({
            ...(current || data || {}),
            ...event.payload.incident,
            summary: {
              ...((current || data || {}).summary || {}),
              status: event.payload.incident.status || (current || data || {}).summary?.status,
              owner: event.payload.incident.owner || event.payload.incident.assigned_to || (current || data || {}).summary?.owner
            }
          }));
        }
      }
    }
  });

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

  useEffect(() => {
    if (!toast) return undefined;
    const timer = window.setTimeout(() => setToast(null), 3200);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const handleExecuteAction = async (action) => {
    if (!incidentId || !action) return;
    if (!status.backendConnected) {
      setToast({ tone: 'error', message: 'Live backend sync is offline, so incident actions are disabled right now.' });
      return;
    }

    const previousIncident = localIncident || data;
    const nextStatus = action.status || previousIncident?.summary?.status || 'INVESTIGATING';
    const nextOwner = previousIncident?.summary?.owner === 'Unassigned' && nextStatus === 'ESCALATED'
      ? 'SOC Tier-1'
      : previousIncident?.summary?.owner;
    const optimisticTimelineEntry = buildTimelineEntry(
      formatActionLabel(action.label),
      `${formatActionLabel(action.label)} was initiated from the incident workspace.`
    );

    setExecutingActionId(action.id);
    setExecutionMessage('');
    setLocalIncident((current) => ({
      ...(current || previousIncident || {}),
      status: nextStatus,
      owner: nextOwner,
      assigned_to: nextOwner,
      summary: {
        ...((current || previousIncident || {}).summary || {}),
        status: nextStatus,
        owner: nextOwner
      },
      timeline: [optimisticTimelineEntry, ...(((current || previousIncident || {}).timeline) || [])]
    }));

    try {
      if (action.status) {
        await updateIncidentStatus(incidentId, action.status);
      }
      if ((previousIncident?.summary?.owner === 'Unassigned' || previousIncident?.owner === 'Unassigned') && action.status === 'ESCALATED') {
        await assignIncident(incidentId, 'SOC Tier-1');
      }
      const successMessage = `${formatActionLabel(action.label)} triggered. Incident status updated to ${action.status || 'in progress'}.`;
      setExecutionMessage(successMessage);
      setToast({ tone: 'success', message: successMessage });
    } catch (error) {
      setLocalIncident(previousIncident || null);
      const errorMessage = error?.message || 'Unable to execute the selected action.';
      setExecutionMessage(errorMessage);
      setToast({ tone: 'error', message: errorMessage });
    } finally {
      setExecutingActionId('');
    }
  };

  const handleExecutePlaybook = async (playbook) => {
    if (!incidentId || !playbook) return;
    if (!status.backendConnected) {
      setToast({ tone: 'error', message: 'Live backend sync is offline, so playbook execution is disabled right now.' });
      return;
    }
    setExecutingActionId(playbook.id);
    setExecutionMessage('');
    try {
      await runPlaybook(incidentId, playbook.id);
      const successMessage = `${playbook.name} launched for ${incidentId}.`;
      setExecutionMessage(successMessage);
      setToast({ tone: 'success', message: successMessage });
    } catch (error) {
      const errorMessage = error?.message || 'Unable to run the recommended playbook.';
      setExecutionMessage(errorMessage);
      setToast({ tone: 'error', message: errorMessage });
    } finally {
      setExecutingActionId('');
    }
  };

  return (
    <RequireAuth allowedRoles={['admin', 'analyst']}>
      <Layout insightSummary={insight}>
        {!incident ? <LoadingSkeleton rows={6} /> : (
          <PageContainer>
            {toast ? (
              <div className={`mb-4 rounded-2xl border px-4 py-3 text-sm ${toast.tone === 'error' ? 'border-[rgba(255,84,81,0.24)] bg-[rgba(147,0,10,0.16)] text-[#ffb4ab]' : 'border-[rgba(74,225,118,0.24)] bg-[rgba(74,225,118,0.12)] text-[#8cf0a8]'}`}>
                {toast.message}
              </div>
            ) : null}
            <PageHeader
              kicker="Incident Detail"
              title={incident.summary.title}
              description="This incident workspace consolidates live evidence, response guidance, and execution controls so analysts can move from triage into action."
              actions={
                <div className="flex flex-wrap items-center gap-3">
                  <SeverityBadge level={incident.summary.severity}>{incident.summary.severity}</SeverityBadge>
                  <StatusIndicator status={status.backendConnected ? 'Live sync active' : 'Hybrid bootstrap'} pulse={status.backendConnected} />
                  <Link href="/investigations" className="soc-btn-secondary">Investigate</Link>
                  <Link href="/threat-graph" className="soc-btn-secondary">Attack graph</Link>
                  <Link href="/playbooks" className="soc-btn-primary">Run playbook</Link>
                </div>
              }
            />

            <ActionRecommendationPanel
              plan={actionPlan}
              executingActionId={executingActionId}
              executionMessage={executionMessage}
              actionDisabled={!status.backendConnected}
              actionDisabledReason="Connect the live backend to execute incident actions."
              onExecuteAction={handleExecuteAction}
              onExecutePlaybook={handleExecutePlaybook}
            />

            <section className="mt-6 grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
              <div className="soc-panel">
                <div className="flex flex-wrap items-center gap-3">
                  <EntityPill type="Owner" label={incident.summary.owner} />
                  <EntityPill type="Confidence" label={incident.summary.confidence} />
                  <EntityPill type="Status" label={incident.summary.status} />
                </div>
                <div className="mt-5 flex flex-wrap gap-2">
                  {incident.summary.users.map((user) => <EntityPill key={user} type="User" label={user} />)}
                  {incident.summary.hosts.map((host) => <EntityPill key={host} type="Host" label={host} />)}
                </div>
                <div className="mt-6">
                  <h2 className="soc-section-title">Incident timeline</h2>
                  <div className="mt-5"><TimelineRail items={incident.timeline} /></div>
                </div>
                <div className="mt-6 rounded-2xl border border-[rgba(173,198,255,0.18)] bg-[rgba(173,198,255,0.06)] px-4 py-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#adc6ff]">Realtime response status</p>
                      <p className="mt-2 text-sm font-semibold text-white">
                        {lastStreamEvent?.type ? formatActionLabel(lastStreamEvent.type) : 'Watching incident stream for response activity'}
                      </p>
                      <p className="mt-2 text-sm leading-6 soc-text-muted">
                        {lastStreamEvent?.payload?.status
                          ? `Latest stream update moved the case to ${lastStreamEvent.payload.status}.`
                          : 'Containment updates and status changes will appear here as they happen.'}
                      </p>
                    </div>
                    <div className="max-w-full">
                      <SeverityBadge level={incident.summary.severity}>{actionPlan.recommendedAction?.label || 'Investigate'}</SeverityBadge>
                    </div>
                  </div>
                </div>
              </div>

              <AIInsightPanel
                title="Narrative intelligence"
                footer={
                  <div className="flex flex-col gap-3 sm:flex-row">
                    <button type="button" className="soc-btn-secondary flex-1" onClick={() => handleExecuteAction({ id: 'escalate-inline', label: 'Escalate incident', status: 'ESCALATED' })}>Escalate</button>
                    <button type="button" className="soc-btn-primary flex-1" onClick={() => handleExecuteAction({ id: 'resolve-inline', label: 'Resolve incident', status: 'RESOLVED' })}>Resolve</button>
                  </div>
                }
              >
                <p>{incident.evidence?.[0]?.content || 'Behavioral evidence is still being compiled.'}</p>
                <p>{incident.evidence?.[2]?.content || 'Attack-path correlation summary is pending.'}</p>
                <p>MITRE coverage: {incident.summary.mitre.join(' | ')}</p>
                <p>{actionPlan.reasoningSummary}</p>
              </AIInsightPanel>
            </section>

            <section className="mt-6 grid gap-6 xl:grid-cols-[0.95fr,1.05fr]">
              <section className="soc-panel">
                <h2 className="soc-section-title">Evidence stack</h2>
                <div className="mt-5"><EvidenceAccordion items={incident.evidence} /></div>
                <h3 className="mt-6 text-base font-semibold text-white">Suggested playbook</h3>
                <div className="mt-4"><PlaybookChecklist steps={actionPlan.recommendedPlaybook?.steps || playbooks?.[0]?.steps || []} /></div>
              </section>
              <GraphPanel graph={graph || { nodes: [], edges: [], chains: [] }} />
            </section>
          </PageContainer>
        )}
      </Layout>
    </RequireAuth>
  );
}

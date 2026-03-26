import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import Layout from '../components/Layout';
import RequireAuth from '../components/RequireAuth';
import LoadingSkeleton from '../components/soc/LoadingSkeleton';
import PageContainer from '../components/soc/PageContainer';
import PlaybookChecklist from '../components/soc/PlaybookChecklist';
import SectionHeader from '../components/soc/SectionHeader';
import StatusBadge from '../components/soc/StatusBadge';
import { runPlaybook } from '../services/api/detectionService';
import { getWorkflowInsight } from '../services/api/insight.service';
import { useHybridData } from '../hooks/useHybridData';

export default function PlaybooksPage() {
  const [execution, setExecution] = useState(null);
  const [insight, setInsight] = useState(null);
  const { data } = useHybridData('playbooks', {}, { bootstrapDelayMs: 8000, pollIntervalMs: 6000 });
  const playbooks = data?.playbooks || [];

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const workflow = await getWorkflowInsight('playbooks');
        if (active) setInsight(workflow);
      } catch {
        if (active) setInsight(null);
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
            eyebrow="Playbooks"
            title="Response Playbooks"
            description="Review and prepare the current SOC response plan."
            actions={<Link href="/reports" className="soc-btn-secondary">Proceed to reports</Link>}
          />

          {!data ? <LoadingSkeleton rows={5} /> : (
            <div className="grid gap-6 xl:grid-cols-[0.95fr,1.05fr]">
              <section className="soc-panel">
                <SectionHeader eyebrow="Catalog" title={playbooks?.[0]?.name || 'No playbook loaded'} />
                <div className="mt-4 flex items-center gap-3">
                  <StatusBadge tone="ready">{playbooks?.length || 0} available</StatusBadge>
                  <button
                    className="soc-btn-primary"
                    onClick={async () => {
                      const result = await runPlaybook('INC-21403', playbooks?.[0]?.id);
                      setExecution(result);
                    }}
                  >
                    Prepare execution
                  </button>
                </div>
                {execution ? (
                  <div className="mt-4 soc-panel-muted">
                    <p className="text-sm font-semibold text-white">{execution.incidentTitle}</p>
                    <p className="mt-2 text-sm leading-6 soc-text-muted">Execution state: {execution.executionStatus}. Started at {execution.startedAt}.</p>
                  </div>
                ) : null}
              </section>
              <section className="soc-panel">
                <SectionHeader eyebrow="Steps" title="Recommended response sequence" />
                <div className="mt-4">
                  <PlaybookChecklist steps={execution?.playbook?.steps || playbooks?.[0]?.steps || []} />
                </div>
              </section>
            </div>
          )}
        </PageContainer>
      </Layout>
    </RequireAuth>
  );
}

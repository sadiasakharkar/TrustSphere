import Link from 'next/link';
import DashboardLayout from '../components/dashboard/DashboardLayout';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import PlaybookChecklist from '../components/soc/PlaybookChecklist';
import RequireAuth from '../components/RequireAuth';
import StatusBadge from '../components/soc/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { useHybridData } from '../hooks/useHybridData';

export default function PlaybooksPage() {
  const { session } = useAuth();
  const { data } = useHybridData('playbooks');
  const playbooks = Array.isArray(data?.playbooks) ? data.playbooks : [];

  return (
    <RequireAuth>
      <DashboardLayout role={session.role}>
        <PageContainer>
          <PageHeader kicker="Response" title="Playbooks" />

          <div className="grid gap-4 xl:grid-cols-2">
            {playbooks.map((playbook) => (
              <section key={playbook.id || playbook.name} className="soc-panel">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div>
                    <p className="soc-kicker">Template</p>
                    <h2 className="soc-section-title">{playbook.name || playbook.title}</h2>
                  </div>
                  <StatusBadge tone="medium">{playbook.threatType || playbook.category || 'mapped'}</StatusBadge>
                </div>
                <PlaybookChecklist steps={playbook.steps || []} />
                <div className="mt-4 flex justify-end">
                  <Link href={`/response?playbook=${encodeURIComponent(playbook.id || playbook.name)}`} className="soc-btn-secondary">Open Response</Link>
                </div>
              </section>
            ))}
          </div>
        </PageContainer>
      </DashboardLayout>
    </RequireAuth>
  );
}

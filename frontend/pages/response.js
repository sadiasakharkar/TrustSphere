import DashboardLayout from '../components/dashboard/DashboardLayout';
import IncidentCard from '../components/soc/IncidentCard';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import RequireAuth from '../components/RequireAuth';
import { useAuth } from '../context/AuthContext';
import { useIncidentApprovals } from '../hooks/useIncidentApprovals';

export default function ResponsePage() {
  const { session } = useAuth();
  const { incidents, currentTime, approveIncident, rejectIncident, modifyIncident } = useIncidentApprovals();

  return (
    <RequireAuth>
      <DashboardLayout role={session.role}>
        <PageContainer>
          <PageHeader kicker="Approval" title="Response Queue" />

          <section className="grid gap-4">
            {incidents.map((incident) => (
              <IncidentCard
                key={incident.id}
                incident={incident}
                role={session.role}
                currentTime={currentTime}
                onApprove={(incidentId) => approveIncident(incidentId, session.username || session.name || 'analyst')}
                onReject={(incidentId) => rejectIncident(incidentId, session.username || session.name || 'analyst')}
                onModify={(incidentId, action) => modifyIncident(incidentId, action, session.username || session.name || 'analyst')}
              />
            ))}
          </section>
        </PageContainer>
      </DashboardLayout>
    </RequireAuth>
  );
}

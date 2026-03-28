import DashboardLayout from '../../components/dashboard/DashboardLayout';
import RequireAuth from '../../components/RequireAuth';
import RoleGuard from '../../components/RoleGuard';
import IncidentCard from '../../components/soc/IncidentCard';
import { useIncidentApprovals } from '../../hooks/useIncidentApprovals';

const cards = [
  { title: 'Health', value: 'Healthy' },
  { title: 'Users', value: '248' },
  { title: 'Risks', value: '21' },
  { title: 'Policy', value: 'Active' },
];

export default function AdminDashboardPage() {
  const { incidents, currentTime } = useIncidentApprovals();

  return (
    <RequireAuth adminOnly>
      <RoleGuard allowedRoles={['admin']} fallback={null}>
        <DashboardLayout role="admin">
          <div id="dashboard" className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {cards.map((item) => (
              <section key={item.title} className="soc-panel">
                <p className="soc-kicker">{item.title}</p>
                <h2 className="soc-section-title">{item.title}</h2>
                <p className="mt-5 text-3xl font-extrabold text-white">{item.value}</p>
              </section>
            ))}
          </div>

          <section id="activity" className="grid gap-4">
            <div>
              <p className="soc-kicker">Audit</p>
              <h2 className="soc-section-title">Trail</h2>
            </div>
            {incidents.map((incident) => (
              <IncidentCard
                key={incident.id}
                incident={incident}
                role="admin"
                currentTime={currentTime}
              />
            ))}
          </section>
          <div id="incidents" className="hidden" />
          <div id="settings" className="hidden" />
        </DashboardLayout>
      </RoleGuard>
    </RequireAuth>
  );
}

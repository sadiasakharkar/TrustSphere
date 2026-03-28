import DashboardLayout from '../components/dashboard/DashboardLayout';
import DataTable from '../components/soc/DataTable';
import PageContainer from '../components/soc/PageContainer';
import PageHeader from '../components/soc/PageHeader';
import RequireAuth from '../components/RequireAuth';
import RoleGuard from '../components/RoleGuard';
import { useAuth } from '../context/AuthContext';
import { useHybridData } from '../hooks/useHybridData';

export default function AdminPage() {
  const { session } = useAuth();
  const { data } = useHybridData('administration');
  const configEntries = Object.entries(data?.systemConfig || {});
  const users = Array.isArray(data?.users) ? data.users : [];

  return (
    <RequireAuth adminOnly>
      <RoleGuard allowedRoles={['admin']} fallback={null}>
        <DashboardLayout role={session.role}>
          <PageContainer>
            <PageHeader kicker="Governance" title="Admin" />

            <div className="grid gap-4 md:grid-cols-3">
              {configEntries.map(([key, value]) => (
                <section key={key} className="soc-panel">
                  <p className="soc-kicker">Config</p>
                  <h2 className="soc-section-title">{key}</h2>
                  <p className="mt-4 text-lg font-semibold text-white">{String(value)}</p>
                </section>
              ))}
            </div>

            <section className="soc-panel">
              <p className="soc-kicker">Users</p>
              <h2 className="soc-section-title">Directory</h2>
              <div className="mt-4">
                <DataTable
                  columns={[
                    { key: 'name', label: 'Name' },
                    { key: 'role', label: 'Role' },
                    { key: 'status', label: 'Status' },
                  ]}
                  rows={users}
                  getRowKey={(row) => row.id}
                  renderCell={(row, key) => <span className="text-sm text-white">{row[key] ?? '--'}</span>}
                />
              </div>
            </section>
          </PageContainer>
        </DashboardLayout>
      </RoleGuard>
    </RequireAuth>
  );
}

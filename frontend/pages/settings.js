import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import Card from '../components/Card';
import Modal from '../components/Modal';
import Table from '../components/Table';
import Badge from '../components/Badge';
import RequireAuth from '../components/RequireAuth';
import { useAuth } from '../context/AuthContext';
import { auditLogs, modelTrainingStatus, users } from '../data/mockData';
import {
  fetchAuditLogs,
  fetchModelTrainingStatus,
  fetchSettings,
  fetchUsers,
  updateUser
} from '../services/apiPlaceholders';

const userColumns = ['Name', 'Role', 'Status', 'Actions'];
const modelColumns = ['Model', 'State', 'ETA', 'Last Run'];
const auditColumns = ['Timestamp', 'Actor', 'Action', 'Result'];

export default function SettingsPage() {
  const { isAdmin } = useAuth();
  const [modal, setModal] = useState({ open: false, title: '', body: '' });

  useEffect(() => {
    fetchSettings();
    if (isAdmin) {
      fetchUsers();
      fetchModelTrainingStatus();
      fetchAuditLogs();
    }
  }, [isAdmin]);

  const openPlaceholder = (title, body) => setModal({ open: true, title, body });

  return (
    <RequireAuth>
      <Layout>
        {!isAdmin && (
          <>
            <Card title="Analyst Settings" subtitle="Personal preferences only in analyst role">
              <div className="grid gap-3 md:grid-cols-2">
                <select className="rounded-lg border border-white/10 bg-bg px-3 py-2">
                  <option>Notification Mode: In-App + SOC email</option>
                  <option>Notification Mode: In-App only</option>
                </select>
                <select className="rounded-lg border border-white/10 bg-bg px-3 py-2">
                  <option>Timezone: UTC +05:30</option>
                  <option>Timezone: UTC +00:00</option>
                </select>
              </div>
              <p className="mt-3 text-xs text-text/70">User management and system configuration are restricted to Admin role.</p>
            </Card>
          </>
        )}

        {isAdmin && (
          <>
            <Card
              className="mb-3"
              title="User Management"
              subtitle="Provision and govern SOC platform users"
              actions={<button className="btn-primary" onClick={() => openPlaceholder('Add User', 'Placeholder form: name, role, status.')}>Add User</button>}
            >
              <Table
                columns={userColumns}
                rows={users}
                rowKey="id"
                renderCell={(row, column) => {
                  if (column === 'Name') return row.name;
                  if (column === 'Role') return row.role;
                  if (column === 'Status') return <Badge tone={row.status === 'Active' ? 'success' : 'high'}>{row.status}</Badge>;
                  if (column === 'Actions') {
                    return (
                      <div className="flex gap-2">
                        <button
                          className="rounded-md border border-white/10 px-3 py-1"
                          onClick={() => {
                            updateUser(row.id, { action: 'edit' });
                            openPlaceholder('Edit User', `Placeholder edit for ${row.name}.`);
                          }}
                        >
                          Edit
                        </button>
                        <button
                          className="rounded-md border border-red-500/40 px-3 py-1 text-red-300"
                          onClick={() => {
                            updateUser(row.id, { action: 'remove' });
                            openPlaceholder('Delete User', `Placeholder delete confirmation for ${row.name}.`);
                          }}
                        >
                          Delete
                        </button>
                      </div>
                    );
                  }
                  return '';
                }}
              />
            </Card>

            <Card id="system" className="mb-3" title="Alert Source Configuration" subtitle="Control local telemetry ingestion sources">
              <div className="grid gap-3 md:grid-cols-2">
                <label className="flex items-center gap-2 rounded-lg border border-white/10 bg-bg/50 p-3"><input type="checkbox" defaultChecked /> SIEM (Splunk)</label>
                <label className="flex items-center gap-2 rounded-lg border border-white/10 bg-bg/50 p-3"><input type="checkbox" defaultChecked /> EDR (CrowdStrike)</label>
                <label className="flex items-center gap-2 rounded-lg border border-white/10 bg-bg/50 p-3"><input type="checkbox" defaultChecked /> IAM Logs</label>
                <label className="flex items-center gap-2 rounded-lg border border-white/10 bg-bg/50 p-3"><input type="checkbox" /> SWIFT Gateway</label>
              </div>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                <select className="rounded-lg border border-white/10 bg-bg px-3 py-2">
                  <option>Model Refresh: Every 6 hours</option>
                  <option>Model Refresh: Every 12 hours</option>
                  <option>Model Refresh: Daily</option>
                </select>
                <select className="rounded-lg border border-white/10 bg-bg px-3 py-2">
                  <option>Data Ingestion: Enabled</option>
                  <option>Data Ingestion: Disabled</option>
                </select>
              </div>
            </Card>

            <Card className="mb-3" title="Model Training Status" subtitle="Offline training pipeline visibility">
              <Table
                columns={modelColumns}
                rows={modelTrainingStatus}
                rowKey="model"
                renderCell={(row, column) => {
                  if (column === 'Model') return row.model;
                  if (column === 'State') {
                    const tone = row.state === 'Running' ? 'violet' : row.state === 'Queued' ? 'high' : 'success';
                    return <Badge tone={tone}>{row.state}</Badge>;
                  }
                  if (column === 'ETA') return row.eta;
                  if (column === 'Last Run') return row.lastRun;
                  return '';
                }}
              />
            </Card>

            <Card id="audit" title="Audit Logs" subtitle="Administrative and AI action traceability">
              <Table
                columns={auditColumns}
                rows={auditLogs}
                rowKey="id"
                renderCell={(row, column) => {
                  if (column === 'Timestamp') return row.timestamp;
                  if (column === 'Actor') return row.actor;
                  if (column === 'Action') return row.action;
                  if (column === 'Result') return <Badge tone="success">{row.result}</Badge>;
                  return '';
                }}
              />
            </Card>
          </>
        )}

        <Modal title={modal.title} open={modal.open} onClose={() => setModal({ open: false, title: '', body: '' })}>
          <p className="text-sm text-text/90">{modal.body}</p>
        </Modal>
      </Layout>
    </RequireAuth>
  );
}

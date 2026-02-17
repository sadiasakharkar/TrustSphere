import { useEffect } from 'react';
import Layout from '../components/Layout';
import { users } from '../data/mockData';
import { fetchSettings, fetchUsers, updateUser } from '../services/apiPlaceholders';

export default function SettingsPage() {
  useEffect(() => {
    fetchUsers();
    fetchSettings();
  }, []);

  return (
    <Layout>
      <section className="card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">User Management</h3>
          <button className="btn-primary" onClick={() => updateUser('new', { action: 'add' })}>Add User</button>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-white/10 text-text/70">
              <tr>
                <th className="px-3 py-2">User ID</th>
                <th className="px-3 py-2">Name</th>
                <th className="px-3 py-2">Role</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-white/5">
                  <td className="px-3 py-3">{user.id}</td>
                  <td className="px-3 py-3">{user.name}</td>
                  <td className="px-3 py-3">{user.role}</td>
                  <td className="px-3 py-3">{user.status}</td>
                  <td className="flex gap-2 px-3 py-3">
                    <button className="rounded-md border border-white/10 px-3 py-1" onClick={() => updateUser(user.id, { action: 'edit' })}>Edit</button>
                    <button className="rounded-md border border-red-500/40 px-3 py-1 text-red-300" onClick={() => updateUser(user.id, { action: 'remove' })}>Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card mt-4 p-4">
        <h3 className="text-lg font-semibold text-white">Alert Source Configuration</h3>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <label className="flex items-center gap-2 rounded-lg border border-white/10 bg-bg/50 p-3">
            <input type="checkbox" defaultChecked /> SIEM (Splunk)
          </label>
          <label className="flex items-center gap-2 rounded-lg border border-white/10 bg-bg/50 p-3">
            <input type="checkbox" defaultChecked /> EDR (CrowdStrike)
          </label>
          <label className="flex items-center gap-2 rounded-lg border border-white/10 bg-bg/50 p-3">
            <input type="checkbox" defaultChecked /> IAM Logs
          </label>
          <label className="flex items-center gap-2 rounded-lg border border-white/10 bg-bg/50 p-3">
            <input type="checkbox" /> SWIFT Gateway
          </label>
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <select className="rounded-lg border border-white/10 bg-bg px-3 py-2">
            <option>Alert Retention: 30 days</option>
            <option>Alert Retention: 90 days</option>
            <option>Alert Retention: 180 days</option>
          </select>
          <select className="rounded-lg border border-white/10 bg-bg px-3 py-2">
            <option>Notification Mode: SOC + Email</option>
            <option>Notification Mode: SOC only</option>
            <option>Notification Mode: Pager + SOC</option>
          </select>
        </div>
      </section>
    </Layout>
  );
}

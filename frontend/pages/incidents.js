import { useMemo, useState } from 'react';
import Layout from '../components/Layout';
import Modal from '../components/Modal';
import { incidents } from '../data/mockData';
import { fetchIncidents, getPlaybook } from '../services/apiPlaceholders';
import { useEffect } from 'react';

export default function IncidentsPage() {
  const [severity, setSeverity] = useState('All');
  const [type, setType] = useState('All');
  const [dateWindow, setDateWindow] = useState('Today');
  const [status, setStatus] = useState('All');
  const [selected, setSelected] = useState(null);
  const [playbookModal, setPlaybookModal] = useState(false);

  useEffect(() => {
    fetchIncidents({ severity, type, dateWindow, status });
  }, [severity, type, dateWindow, status]);

  const filtered = useMemo(
    () =>
      incidents.filter((item) => {
        const bySeverity = severity === 'All' || item.severity === severity;
        const byType = type === 'All' || item.alertType === type;
        const byStatus = status === 'All' || item.status === status;
        return bySeverity && byType && byStatus;
      }),
    [severity, type, status]
  );

  const onGeneratePlaybook = async (row) => {
    setSelected(row);
    setPlaybookModal(true);
    await getPlaybook(row.id);
  };

  return (
    <Layout>
      <div className="card p-4">
        <div className="grid gap-3 md:grid-cols-4">
          <select className="rounded-lg border border-white/10 bg-bg px-3 py-2" value={severity} onChange={(e) => setSeverity(e.target.value)}>
            <option>All</option>
            <option>Critical</option>
            <option>High</option>
            <option>Medium</option>
            <option>Low</option>
          </select>
          <select className="rounded-lg border border-white/10 bg-bg px-3 py-2" value={type} onChange={(e) => setType(e.target.value)}>
            <option>All</option>
            <option>Privilege Escalation</option>
            <option>Anomalous Login</option>
            <option>Malware Signature</option>
            <option>Data Exfiltration</option>
            <option>Phishing</option>
          </select>
          <select className="rounded-lg border border-white/10 bg-bg px-3 py-2" value={dateWindow} onChange={(e) => setDateWindow(e.target.value)}>
            <option>Today</option>
            <option>Last 24 Hours</option>
            <option>Last 7 Days</option>
            <option>Last 30 Days</option>
          </select>
          <select className="rounded-lg border border-white/10 bg-bg px-3 py-2" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option>All</option>
            <option>Investigating</option>
            <option>Open</option>
            <option>Contained</option>
            <option>Escalated</option>
          </select>
        </div>
      </div>

      <div className="card mt-4 overflow-x-auto p-4">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-white/10 text-text/70">
            <tr>
              <th className="px-3 py-2">Timestamp</th>
              <th className="px-3 py-2">User/Host</th>
              <th className="px-3 py-2">Alert Type</th>
              <th className="px-3 py-2">Risk Score</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => (
              <tr key={item.id} className="border-b border-white/5 transition hover:bg-white/5">
                <td className="px-3 py-3">{item.timestamp}</td>
                <td className="px-3 py-3">{item.host}</td>
                <td className="px-3 py-3">{item.alertType}</td>
                <td className="px-3 py-3">
                  <span className="rounded-full bg-accent/20 px-2 py-1 font-semibold text-accent">{item.riskScore}</span>
                </td>
                <td className="px-3 py-3">{item.status}</td>
                <td className="flex gap-2 px-3 py-3">
                  <button className="rounded-md border border-white/10 px-3 py-1 hover:border-accent/60" onClick={() => setSelected(item)}>
                    View Details
                  </button>
                  <button className="rounded-md border border-violet/50 px-3 py-1 hover:bg-violet/20" onClick={() => onGeneratePlaybook(item)}>
                    Generate Playbook
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal title="Incident Details" open={!!selected && !playbookModal} onClose={() => setSelected(null)}>
        {selected && (
          <div className="space-y-2 text-sm">
            <p><span className="text-text/70">Incident ID:</span> {selected.id}</p>
            <p><span className="text-text/70">Host:</span> {selected.host}</p>
            <p><span className="text-text/70">Alert:</span> {selected.alertType}</p>
            <p><span className="text-text/70">Risk Score:</span> {selected.riskScore}</p>
            <p><span className="text-text/70">Status:</span> {selected.status}</p>
          </div>
        )}
      </Modal>

      <Modal title="Playbook Generation" open={playbookModal} onClose={() => setPlaybookModal(false)}>
        <p className="text-sm text-text/90">Playbook draft generated for incident <span className="text-accent">{selected?.id}</span>.</p>
        <div className="mt-4 flex gap-2">
          <button className="btn-primary" onClick={() => setPlaybookModal(false)}>Confirm</button>
          <button className="btn-secondary" onClick={() => setPlaybookModal(false)}>Review</button>
        </div>
      </Modal>
    </Layout>
  );
}

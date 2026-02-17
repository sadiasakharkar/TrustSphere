import { useEffect, useMemo, useState } from 'react';
import Layout from '../components/Layout';
import Modal from '../components/Modal';
import Badge from '../components/Badge';
import Card from '../components/Card';
import Table from '../components/Table';
import RequireAuth from '../components/RequireAuth';
import { incidents } from '../data/mockData';
import { fetchIncidents, getIncidentDetails, getPlaybook } from '../services/apiPlaceholders';

const columns = ['Timestamp', 'User/Host', 'Event Type', 'Risk Score', 'Status', 'Severity', 'Actions'];

const severityTone = {
  Critical: 'critical',
  High: 'high',
  Medium: 'violet',
  Low: 'success'
};

export default function IncidentsPage() {
  const [severity, setSeverity] = useState('All');
  const [type, setType] = useState('All');
  const [dateWindow, setDateWindow] = useState('Today');
  const [status, setStatus] = useState('All');
  const [selected, setSelected] = useState(null);
  const [activeModal, setActiveModal] = useState(null);
  const [playbookState, setPlaybookState] = useState('idle');

  useEffect(() => {
    fetchIncidents({ severity, type, dateWindow, status });
  }, [severity, type, dateWindow, status]);

  const filtered = useMemo(
    () =>
      incidents.filter((item) => {
        const bySeverity = severity === 'All' || item.severity === severity;
        const byType = type === 'All' || item.eventType === type;
        const byStatus = status === 'All' || item.status === status;
        return bySeverity && byType && byStatus;
      }),
    [severity, type, status]
  );

  const openDetails = async (row) => {
    setSelected(row);
    setActiveModal('details');
    await getIncidentDetails(row.id);
  };

  const onGeneratePlaybook = async (row) => {
    setSelected(row);
    setActiveModal('playbook');
    setPlaybookState('loading');
    try {
      await Promise.race([
        getPlaybook(row.id),
        new Promise((resolve) => setTimeout(resolve, 1200))
      ]);
      setPlaybookState('ready');
    } catch {
      setPlaybookState('error');
    }
  };

  const closeModal = () => {
    setActiveModal(null);
    setSelected(null);
    setPlaybookState('idle');
  };

  return (
    <RequireAuth>
      <Layout>
        <Card title="Incident Queue" subtitle="Live placeholder incident telemetry from banking endpoints">
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
        </Card>

        <Card className="mt-3">
          <Table
            columns={columns}
            rows={filtered}
            rowKey="id"
            rowClassName={(row) => (row.severity === 'Critical' ? 'bg-red-500/5' : '')}
            renderCell={(row, column) => {
              if (column === 'Timestamp') return row.timestamp;
              if (column === 'User/Host') return row.entity;
              if (column === 'Event Type') return row.eventType;
              if (column === 'Risk Score') return <Badge tone="info">{row.riskScore}</Badge>;
              if (column === 'Status') return row.status;
              if (column === 'Severity') return <Badge tone={severityTone[row.severity]}>{row.severity}</Badge>;
              if (column === 'Actions') {
                return (
                  <div className="flex flex-wrap gap-2">
                    <button className="rounded-md border border-white/10 px-3 py-1 hover:border-accent/60" onClick={() => openDetails(row)}>
                      View Details
                    </button>
                    <button className="rounded-md border border-violet/50 px-3 py-1 hover:bg-violet/20" onClick={() => onGeneratePlaybook(row)}>
                      Generate Playbook
                    </button>
                  </div>
                );
              }
              return '';
            }}
          />
        </Card>

        <Modal title="Incident Details" open={activeModal === 'details'} onClose={closeModal}>
          {selected && (
            <div className="space-y-2 text-sm">
              <p><span className="text-text/70">Incident ID:</span> {selected.id}</p>
              <p><span className="text-text/70">Timestamp:</span> {selected.timestamp}</p>
              <p><span className="text-text/70">Entity:</span> {selected.entity}</p>
              <p><span className="text-text/70">Event:</span> {selected.eventType}</p>
              <p><span className="text-text/70">Risk Score:</span> {selected.riskScore}</p>
              <p><span className="text-text/70">Affected Assets:</span> {selected.affected}</p>
            </div>
          )}
        </Modal>

        <Modal title="Playbook Generation" open={activeModal === 'playbook'} onClose={closeModal}>
          <p className="text-sm text-text/90">Playbook draft for incident <span className="text-accent">{selected?.id}</span>.</p>
          <div className="mt-4 rounded-lg border border-white/10 bg-bg/60 p-3 text-xs text-text/80">
            {playbookState === 'loading' && 'Generating recommended controls...'}
            {playbookState === 'ready' &&
              'Suggested control set: isolate endpoint, disable token, update IOC signatures, monitor lateral movement channels.'}
            {playbookState === 'error' && 'Playbook generation failed (placeholder). Please retry.'}
          </div>
          <div className="mt-4 flex gap-2">
            <button className="btn-primary" onClick={closeModal}>
              Confirm
            </button>
            <button className="btn-secondary" onClick={closeModal}>
              Review
            </button>
          </div>
        </Modal>
      </Layout>
    </RequireAuth>
  );
}

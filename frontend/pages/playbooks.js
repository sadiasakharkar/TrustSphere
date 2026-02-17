import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import AttackGraphPlaceholder from '../components/AttackGraphPlaceholder';
import PlaybookTimeline from '../components/PlaybookTimeline';
import Modal from '../components/Modal';
import Card from '../components/Card';
import Badge from '../components/Badge';
import RequireAuth from '../components/RequireAuth';
import { playbookSteps } from '../data/mockData';
import { getPlaybook } from '../services/apiPlaceholders';

export default function PlaybooksPage() {
  const [resolveOpen, setResolveOpen] = useState(false);
  const [escalateOpen, setEscalateOpen] = useState(false);

  useEffect(() => {
    getPlaybook('INC-21403');
  }, []);

  return (
    <RequireAuth>
      <Layout>
        <section className="grid gap-3 xl:grid-cols-2">
          <Card title="Incident Summary" subtitle="High-fidelity correlated incident profile">
            <div className="grid gap-2 text-sm md:grid-cols-2">
              <p><span className="text-text/70">ID:</span> INC-21403</p>
              <p><span className="text-text/70">Timestamp:</span> 2026-02-17 10:23:11</p>
              <p><span className="text-text/70">Affected:</span> 3 hosts, 2 users</p>
              <p><span className="text-text/70">Event:</span> Privilege Escalation</p>
              <p><span className="text-text/70">Risk Score:</span> 92</p>
              <p><span className="text-text/70">Severity:</span> <Badge tone="critical">Critical</Badge></p>
            </div>
          </Card>

          <Card title="Narrative Intelligence" subtitle="Human-readable IR brief with MITRE mapping">
            <p className="text-sm text-text/85">
              Initial phishing access targeted finance users, followed by privileged token misuse and rapid lateral movement across payment-adjacent hosts.
              TrustSphere correlated endpoint, IAM, and SIEM events to reconstruct the attack path and score exfiltration risk as critical.
            </p>
            <div className="mt-3 space-y-2 text-xs text-text/75">
              <p>MITRE Techniques: T1566 (Phishing), T1078 (Valid Accounts), T1021 (Remote Services), T1041 (Exfiltration Over C2 Channel)</p>
              <p>Systems Affected: Payroll Segment, Branch Endpoint Cluster, ATM Transfer Bridge</p>
              <p>Fidelity Score: 0.93</p>
            </div>
          </Card>
        </section>

        <section className="mt-3 grid gap-3 xl:grid-cols-2">
          <AttackGraphPlaceholder />
          <PlaybookTimeline steps={playbookSteps} />
        </section>

        <section className="mt-3 flex flex-wrap gap-3">
          <button className="btn-primary" onClick={() => setResolveOpen(true)}>Resolve Incident</button>
          <button className="btn-secondary" onClick={() => setEscalateOpen(true)}>Escalate Incident</button>
        </section>

        <Modal title="Resolve Incident" open={resolveOpen} onClose={() => setResolveOpen(false)}>
          <p className="text-sm">Incident marked as resolved (placeholder). Validation and post-incident review will sync with backend workflow later.</p>
        </Modal>

        <Modal title="Escalate Incident" open={escalateOpen} onClose={() => setEscalateOpen(false)}>
          <p className="text-sm">Escalation package generated for Risk Office and CISO with incident timeline and evidence attachments (placeholder).</p>
        </Modal>
      </Layout>
    </RequireAuth>
  );
}

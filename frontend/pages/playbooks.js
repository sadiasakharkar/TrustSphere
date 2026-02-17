import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import AttackGraphPlaceholder from '../components/AttackGraphPlaceholder';
import PlaybookTimeline from '../components/PlaybookTimeline';
import Modal from '../components/Modal';
import { playbookSteps } from '../data/mockData';
import { getPlaybook } from '../services/apiPlaceholders';

export default function PlaybooksPage() {
  const [resolveOpen, setResolveOpen] = useState(false);
  const [escalateOpen, setEscalateOpen] = useState(false);

  useEffect(() => {
    getPlaybook('INC-21403');
  }, []);

  return (
    <Layout>
      <section className="card p-5">
        <h2 className="text-xl font-bold text-white">Incident Summary</h2>
        <p className="mt-2 text-sm text-text/90">Incident <span className="text-accent">INC-21403</span> originated from compromised privileged credentials and lateral movement attempts on core payment systems.</p>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-2">
        <AttackGraphPlaceholder />
        <PlaybookTimeline steps={playbookSteps} />
      </section>

      <section className="mt-4 flex flex-wrap gap-3">
        <button className="btn-primary" onClick={() => setResolveOpen(true)}>Mark as Resolved</button>
        <button className="btn-secondary" onClick={() => setEscalateOpen(true)}>Escalate Incident</button>
      </section>

      <Modal title="Resolve Incident" open={resolveOpen} onClose={() => setResolveOpen(false)}>
        <p className="text-sm">Resolution event recorded (placeholder). SOC handoff notes can be attached in future backend integration.</p>
      </Modal>

      <Modal title="Escalate Incident" open={escalateOpen} onClose={() => setEscalateOpen(false)}>
        <p className="text-sm">Escalation notification queued to Risk Office and CISO group (placeholder).</p>
      </Modal>
    </Layout>
  );
}

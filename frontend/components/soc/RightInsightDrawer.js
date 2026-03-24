import AIInsightPanel from './AIInsightPanel';
import SeverityBadge from './SeverityBadge';

export default function RightInsightDrawer({ open, summary }) {
  return (
    <aside className={`fixed right-0 top-0 z-20 h-screen w-[22rem] border-l border-[rgba(65,71,85,0.55)] bg-[rgba(16,20,26,0.96)] px-4 py-6 shadow-card transition-transform duration-300 ${open ? 'translate-x-0' : 'translate-x-full'}`}>
      <AIInsightPanel title="AI Copilot Brief">
        <p>{summary?.title || 'Unified intelligence summary is available for the active view.'}</p>
        <div className="grid gap-3 pt-2">
          <div className="soc-panel-muted">
            <p className="text-xs uppercase tracking-[0.16em] text-[rgba(193,198,215,0.55)]">Current posture</p>
            <div className="mt-3 flex items-center justify-between">
              <p className="text-sm font-semibold text-white">Operationally elevated</p>
              <SeverityBadge level="high">High</SeverityBadge>
            </div>
          </div>
          <div className="soc-panel-muted">
            <p className="text-xs uppercase tracking-[0.16em] text-[rgba(193,198,215,0.55)]">Recommended next action</p>
            <p className="mt-3 text-sm text-white">Confirm containment approval, then pivot to threat graph to validate lateral movement scope.</p>
          </div>
        </div>
      </AIInsightPanel>
    </aside>
  );
}

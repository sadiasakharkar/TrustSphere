import StatusBadge from './StatusBadge';

export default function GraphPanel({ graph }) {
  return (
    <section className="soc-grid-bg overflow-hidden">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="soc-kicker">Threat Graph</p>
          <h3 className="soc-section-title">Correlated attacker movement</h3>
        </div>
        <StatusBadge tone="critical">2 active chains</StatusBadge>
      </div>
      <div className="relative min-h-[360px] rounded-xl border border-[rgba(65,71,85,0.45)] bg-[rgba(10,14,20,0.78)]">
        {graph.nodes.map((node) => (
          <div
            key={node.id}
            className="absolute flex flex-col items-center gap-2"
            style={{ left: `${node.x}%`, top: `${node.y}%`, transform: 'translate(-50%, -50%)' }}
          >
            <div className={`flex h-12 w-12 items-center justify-center rounded-xl border text-xs font-bold ${node.risk === 'critical' ? 'border-[rgba(255,84,81,0.5)] bg-[rgba(147,0,10,0.15)] text-[#ffb4ab]' : 'border-[rgba(173,198,255,0.45)] bg-[rgba(75,142,255,0.12)] text-[#adc6ff]'}`}>
              {node.type.slice(0, 1).toUpperCase()}
            </div>
            <span className="rounded-md bg-[rgba(28,32,38,0.9)] px-2 py-1 text-[10px] font-mono text-white">{node.label}</span>
          </div>
        ))}
        <svg className="absolute inset-0 h-full w-full">
          {graph.edges.map((edge, index) => {
            const from = graph.nodes.find((node) => node.id === edge.from);
            const to = graph.nodes.find((node) => node.id === edge.to);
            if (!from || !to) return null;
            return <line key={`${edge.from}-${edge.to}-${index}`} x1={`${from.x}%`} y1={`${from.y}%`} x2={`${to.x}%`} y2={`${to.y}%`} stroke="rgba(173,198,255,0.45)" strokeWidth="2" strokeDasharray="6 5" />;
          })}
        </svg>
      </div>
    </section>
  );
}

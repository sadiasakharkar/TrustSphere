export default function Topbar() {
  return (
    <header className="sticky top-0 z-30 mb-5 flex h-16 items-center justify-between rounded-xl border border-white/10 bg-panel/90 px-4 shadow-card backdrop-blur">
      <div className="relative w-full max-w-md">
        <input
          type="text"
          placeholder="Search alerts, hosts, users..."
          className="w-full rounded-lg border border-white/10 bg-bg/80 px-4 py-2 text-sm outline-none ring-accent/40 transition focus:ring"
        />
      </div>

      <div className="ml-4 flex items-center gap-3">
        <button className="rounded-lg border border-white/10 bg-bg/60 px-3 py-2 text-sm hover:border-accent/60">Notifications</button>
        <div className="rounded-lg border border-white/10 px-3 py-2 text-sm text-white">SOC Admin</div>
      </div>
    </header>
  );
}

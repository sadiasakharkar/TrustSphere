import { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { session, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const router = useRouter();

  return (
    <header className="sticky top-0 z-30 mb-3 rounded-xl border border-white/10 bg-panel/90 p-3 shadow-card backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-full max-w-md">
          <input
            type="text"
            placeholder="Search incidents, entities, tactics..."
            className="w-full rounded-lg border border-white/10 bg-bg/80 px-4 py-2 text-sm outline-none ring-accent/40 transition focus:ring"
          />
        </div>

        <div className="flex items-center gap-2">
          <button className="group relative rounded-lg border border-white/10 bg-bg/70 px-3 py-2 text-sm hover:border-accent/70">
            Notifications
            <span className="absolute -right-1 -top-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] text-white">
              7
            </span>
          </button>

          <div className="relative">
            <button
              className="rounded-lg border border-white/10 bg-bg/70 px-3 py-2 text-sm text-white hover:border-secondary/70"
              onClick={() => setOpen((prev) => !prev)}
            >
              {session.username} ({session.role})
            </button>
            {open && (
              <div className="absolute right-0 mt-2 w-52 rounded-lg border border-white/10 bg-panel p-2 shadow-card">
                <button
                  className="w-full rounded-md px-3 py-2 text-left text-sm hover:bg-white/5"
                  onClick={() => {
                    setOpen(false);
                    router.push('/settings');
                  }}
                >
                  Open Settings
                </button>
                <button
                  className="w-full rounded-md px-3 py-2 text-left text-sm text-red-300 hover:bg-red-500/10"
                  onClick={() => {
                    logout();
                    router.push('/login');
                  }}
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

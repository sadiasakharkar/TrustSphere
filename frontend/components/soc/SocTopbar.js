import { useRouter } from 'next/router';
import { useAuth } from '../../context/AuthContext';
import StatusIndicator from './StatusIndicator';

export default function SocTopbar({ onMenu }) {
  const { session, logout } = useAuth();
  const router = useRouter();

  return (
    <header className="soc-topbar">
      <div className="flex flex-1 items-center gap-3">
        <button className="soc-btn-ghost lg:hidden" onClick={onMenu} aria-label="Open navigation">
          <span className="material-symbols-outlined">menu</span>
        </button>
        <div className="relative w-full max-w-[420px]">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[rgba(193,198,215,0.5)]">search</span>
          <input className="soc-input pl-10" placeholder="Search incidents, assets, IPs, or users" />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-3 rounded-full border border-[rgba(65,71,85,0.55)] bg-[rgba(28,32,38,0.9)] px-3 py-2 md:flex">
          <StatusIndicator status="Air-gapped" pulse />
          <div className="h-4 w-px bg-[rgba(65,71,85,0.55)]" />
          <StatusIndicator status="Inference healthy" />
        </div>
        <button className="soc-btn-secondary hidden sm:inline-flex" onClick={() => router.push('/settings')}>
          <span className="material-symbols-outlined">manage_accounts</span>
          {session.role}
        </button>
        <button
          className="soc-btn-ghost"
          onClick={() => {
            logout();
            router.push('/login');
          }}
          aria-label="Logout"
        >
          <span className="material-symbols-outlined">logout</span>
        </button>
      </div>
    </header>
  );
}

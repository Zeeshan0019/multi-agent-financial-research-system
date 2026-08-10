import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const NAV = [
  { to: "/", label: "Dashboard", icon: DashboardIcon, color: "#8B5CF6" },
  { to: "/upload", label: "Upload", icon: UploadIcon, color: "#14B8A6" },
  { to: "/research", label: "Research", icon: ResearchIcon, color: "#F5A524" },
  { to: "/comparison", label: "Comparison", icon: ComparisonIcon, color: "#FB7185" },
  { to: "/reports", label: "Reports", icon: ReportsIcon, color: "#8B5CF6" },
];

export default function Layout({ children }) {
  const { user, logOut } = useAuth();

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-64 shrink-0 flex-col bg-white border-r border-slate-200/80 shadow-[4px_0_24px_rgba(30,27,60,0.02)] text-ledger-950 z-10">
        {/* Logo */}
        <div className="px-6 pt-7 pb-6">
          <div className="flex items-center gap-3">
            <span
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl font-display text-base font-bold text-white shadow-md shadow-violet-200"
              style={{ background: "linear-gradient(135deg, #8B5CF6 0%, #14B8A6 100%)" }}
            >
              M
            </span>
            <div>
              <span className="font-display text-[0.75rem] font-extrabold tracking-tight bg-clip-text text-transparent bg-brand-gradient uppercase leading-none block">
                Multi-Agent
              </span>
              <p className="text-[0.55rem] font-bold leading-snug tracking-wider text-ledger-950/50 uppercase mt-0.5 whitespace-nowrap">
                Financial Research System
              </p>
            </div>
          </div>
        </div>

        <div className="mx-6 border-t border-slate-100" />

        {/* Navigation */}
        <nav className="flex flex-col gap-1 px-4 py-6">
          {NAV.map(({ to, label, icon: Icon, color }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `group relative flex items-center gap-3.5 rounded-xl px-4 py-3 text-sm font-semibold transition-all duration-200 ${
                  isActive
                    ? "bg-violet-50/70 text-violet-700 shadow-sm border border-violet-100/20"
                    : "text-ledger-950/65 hover:bg-slate-50/80 hover:text-ledger-950"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className="absolute left-0 top-1/2 h-5 w-[3.5px] -translate-y-1/2 rounded-full transition-all duration-300"
                    style={{
                      background: color,
                      opacity: isActive ? 1 : 0,
                      transform: `translateY(-50%) scaleY(${isActive ? 1 : 0.3})`,
                    }}
                  />
                  <span className="relative flex items-center justify-center">
                    <Icon color={isActive ? color : undefined} />
                  </span>
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* User info + logout at bottom */}
        <div className="mt-auto px-4 pb-6">
          <div className="mx-2 mb-4 border-t border-slate-100" />
          <div className="rounded-xl border border-slate-200 bg-slate-50/50 px-3 py-3 flex items-center gap-3">
            <div
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full font-bold text-xs text-white shadow-sm"
              style={{ background: "linear-gradient(135deg, #8B5CF6 0%, #14B8A6 100%)" }}
            >
              {user?.username?.[0]?.toUpperCase() || "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold text-ledger-950 truncate">{user?.username || "User"}</p>
              <p className="text-[0.6rem] font-semibold text-ledger-950/40 uppercase tracking-wide">Signed in</p>
            </div>
            <button
              onClick={logOut}
              title="Sign out"
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-ledger-950/40 hover:bg-rose-50 hover:text-rose-500 transition-all duration-200"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      <main className="min-h-screen flex-1 bg-parchment-100">
        <div className="mx-auto max-w-6xl px-8 py-8">{children}</div>
      </main>
    </div>
  );
}

function iconProps(color) {
  return { width: 17, height: 17, viewBox: "0 0 24 24", fill: "none", stroke: color || "currentColor", strokeWidth: 1.75, strokeLinecap: "round", strokeLinejoin: "round", style: { transition: "stroke 0.2s ease" } };
}
function DashboardIcon({ color }) {
  return (
    <svg {...iconProps(color)}>
      <rect x="3" y="3" width="7" height="9" rx="1" />
      <rect x="14" y="3" width="7" height="5" rx="1" />
      <rect x="14" y="12" width="7" height="9" rx="1" />
      <rect x="3" y="16" width="7" height="5" rx="1" />
    </svg>
  );
}
function UploadIcon({ color }) {
  return (
    <svg {...iconProps(color)}>
      <path d="M12 16V4" />
      <path d="M6 10l6-6 6 6" />
      <path d="M4 20h16" />
    </svg>
  );
}
function ResearchIcon({ color }) {
  return (
    <svg {...iconProps(color)}>
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.3-4.3" />
    </svg>
  );
}
function ComparisonIcon({ color }) {
  return (
    <svg {...iconProps(color)}>
      <path d="M7 3v18" />
      <path d="M17 3v18" />
      <path d="M3 8h4" />
      <path d="M17 16h4" />
      <path d="M3 14h4" />
      <path d="M17 8h4" />
    </svg>
  );
}
function ReportsIcon({ color }) {
  return (
    <svg {...iconProps(color)}>
      <path d="M6 2h9l5 5v15H6z" />
      <path d="M15 2v5h5" />
      <path d="M9 13h6" />
      <path d="M9 17h6" />
    </svg>
  );
}

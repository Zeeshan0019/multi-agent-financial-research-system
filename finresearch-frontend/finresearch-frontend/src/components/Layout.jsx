import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useSession } from "../context/SessionContext.jsx";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: "◧" },
  { to: "/upload", label: "Upload", icon: "↑" },
  { to: "/research", label: "Research", icon: "≡" },
  { to: "/comparison", label: "Comparison", icon: "⇄" },
  { to: "/reports", label: "Reports", icon: "▤" },
];

export default function Layout() {
  const { activeSessionName } = useSession();

  return (
    <div className="min-h-screen flex bg-parchment-50">
      <aside className="w-60 shrink-0 bg-ledger-950 text-parchment-100 flex flex-col">
        <div className="px-5 py-6 border-b border-white/10">
          <div className="flex items-center gap-2">
            <span className="text-amber-500 font-serif text-2xl leading-none">§</span>
            <span className="font-serif text-lg tracking-tight">Ledger</span>
          </div>
          <p className="text-[11px] text-parchment-100/50 mt-1">
            Multi-agent financial research
          </p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                  isActive
                    ? "bg-white/10 text-white font-medium"
                    : "text-parchment-100/70 hover:bg-white/5 hover:text-white"
                }`
              }
            >
              <span className="w-4 text-center text-amber-500/80">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-4 py-4 border-t border-white/10 text-[11px] text-parchment-100/50">
          Active session
          <div className="text-parchment-100 text-sm font-medium truncate">
            {activeSessionName || "None selected"}
          </div>
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        <Outlet />
      </main>
    </div>
  );
}

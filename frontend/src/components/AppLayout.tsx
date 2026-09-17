import { NavLink, Outlet, Link } from "react-router-dom";
import { LayoutDashboard, FileStack, ListChecks, GitCompareArrows, MessageCircleQuestion, BarChart3, ArrowLeft } from "lucide-react";
import clsx from "clsx";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/documents", label: "Documents", icon: FileStack },
  { to: "/review-queue", label: "Review Queue", icon: ListChecks },
  { to: "/compare", label: "Compare", icon: GitCompareArrows },
  { to: "/ask", label: "Ask VeriDoc", icon: MessageCircleQuestion },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
];

export function AppLayout() {
  return (
    <div className="min-h-screen flex bg-canvas">
      <aside className="w-60 shrink-0 border-r border-line bg-surface hidden md:flex flex-col">
        <div className="h-16 flex items-center px-5 border-b border-line">
          <Link to="/" className="flex items-center gap-2 font-semibold text-ink">
            <span className="h-7 w-7 rounded-lg bg-brand-deep flex items-center justify-center text-white text-sm">V</span>
            VeriDoc
          </Link>
        </div>
        <nav className="flex-1 py-4 px-3 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors",
                  isActive ? "bg-brand-pastel text-brand-deep font-medium" : "text-inkmuted hover:bg-canvas hover:text-ink"
                )
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-line space-y-1">
          <Link to="/" className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-inkmuted hover:text-ink">
            <ArrowLeft size={17} />
            Back to site
          </Link>
        </div>
      </aside>
      <main className="flex-1 min-w-0">
        <div className="md:hidden h-14 border-b border-line bg-surface flex items-center px-4 gap-3 overflow-x-auto sticky top-0 z-30">
          {NAV_ITEMS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx("text-xs whitespace-nowrap px-2.5 py-1.5 rounded-full", isActive ? "bg-brand-pastel text-brand-deep font-medium" : "text-inkmuted")
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
        <Outlet />
      </main>
    </div>
  );
}

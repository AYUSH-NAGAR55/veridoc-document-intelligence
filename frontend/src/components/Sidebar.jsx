import { NavLink } from "react-router-dom";
import { FileStack, ShieldCheck, LayoutDashboard } from "lucide-react";

export default function Sidebar({ documents }) {
  const reviewCount = documents.filter((d) => d.status === "needs_review").length;

  return (
    <aside className="w-64 shrink-0 border-r border-border bg-surface/60 flex flex-col h-screen sticky top-0">
      <div className="px-5 pt-6 pb-5 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-primary-soft flex items-center justify-center">
            <ShieldCheck size={17} className="text-primary-deep" />
          </div>
          <div>
            <h1 className="font-display text-lg leading-none text-ink">VeriDoc</h1>
            <p className="text-[11px] text-ink-soft mt-0.5">Verified document knowledge</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            `flex items-center gap-2.5 px-3 py-2 rounded-xl2 text-sm font-medium transition-colors ${
              isActive ? "bg-primary-soft text-primary-deep" : "text-ink-soft hover:bg-paper hover:text-ink"
            }`
          }
        >
          <LayoutDashboard size={16} />
          Dashboard
        </NavLink>
        <NavLink
          to="/documents"
          className={({ isActive }) =>
            `flex items-center gap-2.5 px-3 py-2 rounded-xl2 text-sm font-medium transition-colors ${
              isActive ? "bg-primary-soft text-primary-deep" : "text-ink-soft hover:bg-paper hover:text-ink"
            }`
          }
        >
          <FileStack size={16} />
          Documents
        </NavLink>
      </nav>

      <div className="px-5 py-4 border-t border-border">
        {reviewCount > 0 ? (
          <div className="rounded-xl2 bg-amber-soft px-3 py-2.5 text-xs text-[#7A5326]">
            <span className="font-semibold">{reviewCount}</span> document{reviewCount !== 1 ? "s" : ""} waiting on review
          </div>
        ) : (
          <p className="text-[11px] text-ink-soft">Nothing needs your review right now.</p>
        )}
      </div>
    </aside>
  );
}

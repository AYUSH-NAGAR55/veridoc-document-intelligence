import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import { Menu, X } from "lucide-react";

const LINKS = [
  { to: "/#how-it-works", label: "How it works" },
  { to: "/about", label: "About" },
  { to: "/faq", label: "FAQ" },
  { to: "/contact", label: "Contact" },
];

export function PublicNav() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  return (
    <header className="sticky top-0 z-40 bg-canvas/85 backdrop-blur border-b border-line">
      <div className="container-page flex items-center justify-between h-16">
        <Link to="/" className="flex items-center gap-2 font-semibold text-ink">
          <span className="h-7 w-7 rounded-lg bg-brand-deep flex items-center justify-center text-white text-sm">V</span>
          VeriDoc
        </Link>
        <nav className="hidden md:flex items-center gap-7 text-sm text-inkmuted">
          {LINKS.map((l) => (
            <Link key={l.to} to={l.to} className="hover:text-ink transition-colors">
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="hidden md:flex items-center gap-3">
          <Link to="/documents" className="text-sm text-inkmuted hover:text-ink transition-colors">
            View documents
          </Link>
          <Link
            to="/documents?upload=1"
            className="bg-brand-deep text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-brand-deep/90 transition-colors"
          >
            Upload a document
          </Link>
        </div>
        <button className="md:hidden" onClick={() => setOpen(!open)} aria-label="Toggle menu">
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>
      {open && (
        <div className="md:hidden border-t border-line bg-canvas px-6 py-4 space-y-3">
          {LINKS.map((l) => (
            <Link key={l.to} to={l.to} className="block text-sm text-inkmuted" onClick={() => setOpen(false)}>
              {l.label}
            </Link>
          ))}
          <Link to="/documents?upload=1" className="block text-sm font-medium text-brand-deep" onClick={() => setOpen(false)}>
            Upload a document
          </Link>
        </div>
      )}
    </header>
  );
}

import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ShieldCheck, ScanSearch, GitCompareArrows, Layers, FileSearch } from "lucide-react";
import { PublicNav } from "../components/PublicNav";
import { DocStackHero } from "../components/DocStackHero";
import { PipelineProgress } from "../components/PipelineProgress";

const FORMATS = ["PDF", "DOCX", "TXT", "CSV", "JSON", "PNG / JPG", "Scanned PDFs"];

const FEATURES = [
  {
    icon: ShieldCheck,
    title: "Independent validation",
    body: "Arithmetic, dates, and cross-field consistency are checked by deterministic Python logic — not just the model's own confidence.",
  },
  {
    icon: ScanSearch,
    title: "Source-grounded answers",
    body: "Every answer points back to a page, section, row, or line. If it isn't in your documents, VeriDoc says so instead of guessing.",
  },
  {
    icon: Layers,
    title: "A knowledge ladder, not a black box",
    body: "Raw text becomes extracted data, then validated data, then reviewed data, then verified knowledge — each step is visible.",
  },
  {
    icon: GitCompareArrows,
    title: "Compare and cross-check",
    body: "Diff two reports, or check an invoice against its purchase order and delivery receipt for mismatches.",
  },
];

const FAQS = [
  {
    q: "Does VeriDoc work without setting up an LLM API key?",
    a: "Yes. VeriDoc ships with an offline demo mode so you can try the full workflow before connecting a provider.",
  },
  {
    q: "What happens to a low-confidence extraction?",
    a: "It's routed to the Review Queue instead of being marked verified automatically, and needs a human decision — accept, correct, or reject.",
  },
  {
    q: "Can VeriDoc read scanned documents?",
    a: "Yes. Pages with little or no extractable text are automatically rendered and run through OCR.",
  },
  {
    q: "Where does verified information come from?",
    a: "Only from your uploaded documents. Answers are built from retrieved, cited passages — VeriDoc doesn't draw on outside knowledge.",
  },
];

export default function Landing() {
  return (
    <div>
      <PublicNav />

      {/* Hero */}
      <section className="container-page pt-16 pb-8 grid md:grid-cols-2 gap-10 items-center">
        <div>
          <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-ink leading-[1.08]">
            Turn documents into <span className="text-brand-deep">verified</span> knowledge.
          </h1>
          <p className="mt-5 text-lg text-inkmuted max-w-md">
            Extract. Validate. Verify. Search. Ask. VeriDoc reads your documents, checks its own
            work, and shows exactly where every answer came from.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/documents?upload=1" className="bg-brand-deep text-white font-medium px-5 py-3 rounded-lg hover:bg-brand-deep/90 transition-colors">
              Upload a document
            </Link>
            <Link to="/documents" className="border border-line bg-surface px-5 py-3 rounded-lg font-medium text-ink hover:border-brand-deep/60 transition-colors">
              Explore demo documents
            </Link>
          </div>
        </div>
        <DocStackHero />
      </section>

      {/* How it works */}
      <section id="how-it-works" className="container-page py-16 border-t border-line">
        <h2 className="text-2xl font-semibold text-ink">How VeriDoc works</h2>
        <p className="text-inkmuted mt-2 max-w-lg">
          A document doesn't become "knowledge" the moment it's uploaded — it earns that status by
          passing through every stage below.
        </p>
        <div className="mt-8 bg-surface border border-line rounded-xl2 p-6 overflow-x-auto">
          <PipelineProgress status="ready" />
        </div>
      </section>

      {/* Supported formats */}
      <section className="container-page py-16 border-t border-line">
        <h2 className="text-2xl font-semibold text-ink">Any document format, handled natively</h2>
        <p className="text-inkmuted mt-2 max-w-lg">
          VeriDoc doesn't force every file to pretend it has pages. A CSV keeps its rows and
          columns; a scanned PDF gets OCR only where it's actually needed.
        </p>
        <div className="mt-6 flex flex-wrap gap-2.5">
          {FORMATS.map((f) => (
            <span key={f} className="bg-lavender-pastel text-lavender-deep text-sm font-medium px-3.5 py-1.5 rounded-full">
              {f}
            </span>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="container-page py-16 border-t border-line">
        <h2 className="text-2xl font-semibold text-ink">Verification is the point</h2>
        <div className="mt-8 grid sm:grid-cols-2 gap-5">
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 8 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.4 }}
              className="bg-surface border border-line rounded-xl2 p-6"
            >
              <div className="h-10 w-10 rounded-lg bg-mint-pastel text-mint-deep flex items-center justify-center mb-4">
                <Icon size={18} />
              </div>
              <h3 className="font-semibold text-ink">{title}</h3>
              <p className="text-sm text-inkmuted mt-1.5 leading-relaxed">{body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Example workflow */}
      <section className="container-page py-16 border-t border-line">
        <h2 className="text-2xl font-semibold text-ink">A grounded answer, end to end</h2>
        <div className="mt-8 grid md:grid-cols-2 gap-6">
          <div className="bg-surface border border-line rounded-xl2 p-6">
            <p className="text-sm text-inkmuted mb-2 flex items-center gap-1.5"><FileSearch size={15}/> Question</p>
            <p className="font-medium text-ink">"What was the company's revenue in 2025?"</p>
          </div>
          <div className="bg-surface border border-line rounded-xl2 p-6 space-y-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-inkmuted">Answer</p>
              <p className="font-medium text-ink mt-1">₹428.6 crore</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-inkmuted">Source</p>
              <p className="text-sm text-ink mt-1">Page 17 — Financial Summary, Table 2</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-inkmuted">Confidence</p>
              <p className="text-sm font-mono text-mint-deep mt-1">96%</p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="container-page py-16 border-t border-line">
        <h2 className="text-2xl font-semibold text-ink">Frequently asked questions</h2>
        <div className="mt-8 divide-y divide-line border-t border-b border-line">
          {FAQS.map((f) => (
            <details key={f.q} className="group py-4">
              <summary className="flex items-center justify-between cursor-pointer list-none font-medium text-ink">
                {f.q}
                <span className="text-inkmuted group-open:rotate-45 transition-transform">+</span>
              </summary>
              <p className="text-sm text-inkmuted mt-2 leading-relaxed">{f.a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="container-page py-20 border-t border-line text-center">
        <h2 className="text-2xl md:text-3xl font-semibold text-ink">Ready to see what your documents actually say?</h2>
        <div className="mt-6 flex justify-center gap-3">
          <Link to="/documents?upload=1" className="bg-brand-deep text-white font-medium px-6 py-3 rounded-lg hover:bg-brand-deep/90 transition-colors">
            Upload a document
          </Link>
          <Link to="/dashboard" className="border border-line bg-surface px-6 py-3 rounded-lg font-medium text-ink hover:border-brand-deep/60 transition-colors">
            View dashboard
          </Link>
        </div>
      </section>

      <footer className="border-t border-line">
        <div className="container-page py-10 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-inkmuted">
          <p>© {new Date().getFullYear()} VeriDoc. Built for document intelligence you can trust.</p>
          <div className="flex gap-5">
            <Link to="/about" className="hover:text-ink">About</Link>
            <Link to="/contact" className="hover:text-ink">Contact</Link>
            <Link to="/faq" className="hover:text-ink">FAQ</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

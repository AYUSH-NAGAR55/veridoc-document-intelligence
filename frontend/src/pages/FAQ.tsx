import { PublicNav } from "../components/PublicNav";

const FAQS = [
  { q: "Is VeriDoc limited to PDFs?", a: "No — it natively handles PDF, DOCX, TXT, CSV, JSON, and images, each with format-appropriate provenance (page, section, row, or line)." },
  { q: "How does VeriDoc avoid hallucinated answers?", a: "Answers are generated only from retrieved, cited passages of your verified documents. If nothing relevant is found, VeriDoc says so instead of guessing." },
  { q: "What triggers human review?", a: "Any field below the confidence threshold, or any field that fails an independent validation check (e.g. numbers that don't add up), is routed to the Review Queue." },
  { q: "Can I correct an AI extraction?", a: "Yes. Corrections are stored alongside the original AI value with a full audit trail — nothing is silently overwritten." },
  { q: "Can I compare two versions of a report?", a: "Yes, the Compare page shows exactly which verified values changed, were added, or were removed between two documents." },
  { q: "What LLM providers are supported?", a: "Any OpenAI-compatible API, Ollama for local development, or a fully offline demo mode that requires no API key." },
];

export default function FAQ() {
  return (
    <div>
      <PublicNav />
      <section className="container-page py-16 max-w-2xl">
        <h1 className="text-3xl font-semibold text-ink">Frequently asked questions</h1>
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
    </div>
  );
}

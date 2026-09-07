import { PublicNav } from "../components/PublicNav";
import { Link } from "react-router-dom";

export default function About() {
  return (
    <div>
      <PublicNav />
      <section className="container-page py-16 max-w-2xl">
        <h1 className="text-3xl font-semibold text-ink">About VeriDoc</h1>
        <p className="text-inkmuted mt-4 leading-relaxed">
          Most "chat with your PDF" tools skip straight from upload to answer. VeriDoc adds the
          steps that make an answer trustworthy: independent validation, confidence scoring, a
          human review step for anything uncertain, and a verified-knowledge layer that RAG reads
          from — not the raw, unchecked extraction.
        </p>
        <p className="text-inkmuted mt-4 leading-relaxed">
          The result is a system that can say "I don't know" instead of guessing, and that can
          always show you exactly which page, row, or line an answer came from.
        </p>
        <h2 className="text-xl font-semibold text-ink mt-10">What VeriDoc is built on</h2>
        <ul className="mt-3 space-y-2 text-inkmuted list-disc pl-5">
          <li>A FastAPI + Python backend for document processing, validation, and RAG</li>
          <li>Sentence-Transformers embeddings and FAISS for retrieval</li>
          <li>An LLM provider abstraction — OpenAI-compatible, Ollama, or fully offline demo mode</li>
          <li>A React + TypeScript frontend focused on transparency over spectacle</li>
        </ul>
        <Link to="/contact" className="inline-block mt-10 text-blue-deep font-medium">
          Get in touch →
        </Link>
      </section>
    </div>
  );
}

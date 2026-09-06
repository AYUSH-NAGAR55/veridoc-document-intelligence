import { useEffect, useState } from "react";
import { Send, FileText } from "lucide-react";
import { api } from "../api/client";
import { ConfidenceBadge, EmptyState } from "../components/shared";
import { useToast } from "../components/Toast";

export default function AskVeriDoc() {
  const [docs, setDocs] = useState<any[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState<{ question: string; result: any }[]>([]);
  const [asking, setAsking] = useState(false);
  const toast = useToast();

  useEffect(() => {
    api.listDocuments({ status: "ready" }).then(setDocs);
  }, []);

  const toggleDoc = (id: string) => setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const ask = async () => {
    if (!question.trim()) return;
    setAsking(true);
    try {
      const result = await api.query(question, selectedIds.length ? selectedIds : undefined);
      setHistory((prev) => [{ question, result }, ...prev]);
      setQuestion("");
    } catch (e: any) {
      toast.show(e.message, "error");
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-4xl">
      <h1 className="text-2xl font-semibold text-ink">Ask VeriDoc</h1>
      <p className="text-inkmuted text-sm mt-1 mb-6">
        Ask across all your documents, or narrow to a specific set — e.g. "What was revenue growth between 2024 and 2026?"
      </p>

      {docs.length === 0 ? (
        <div className="bg-surface border border-line rounded-xl2">
          <EmptyState icon={<FileText size={26} />} title="No ready documents yet." description="Upload and process a document before asking questions." />
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-2 mb-4">
            {docs.map((d) => (
              <button
                key={d.id}
                onClick={() => toggleDoc(d.id)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                  selectedIds.includes(d.id) ? "bg-blue-deep text-white border-blue-deep" : "bg-surface text-inkmuted border-line"
                }`}
              >
                {d.filename}
              </button>
            ))}
            {selectedIds.length === 0 && <span className="text-xs text-inkmuted self-center">(none selected = search across all documents)</span>}
          </div>

          <div className="flex gap-2 mb-6">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && ask()}
              placeholder="Ask a question..."
              className="flex-1 border border-line rounded-lg px-3.5 py-2.5 bg-surface text-sm focus:border-blue-deep outline-none"
            />
            <button onClick={ask} disabled={asking} className="bg-blue-deep text-white px-4 py-2.5 rounded-lg flex items-center gap-1.5 text-sm font-medium disabled:opacity-60">
              <Send size={15} /> {asking ? "Thinking..." : "Ask"}
            </button>
          </div>

          <div className="space-y-4">
            {history.map((h, i) => (
              <div key={i} className="bg-surface border border-line rounded-xl2 p-5">
                <p className="text-sm font-medium text-ink">{h.question}</p>
                <p className="text-ink mt-2">{h.result.answer}</p>
                {h.result.grounded && (
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <ConfidenceBadge value={h.result.confidence} />
                    {h.result.sources.map((s: any, si: number) => (
                      <span key={si} className="text-xs bg-canvas text-inkmuted px-2.5 py-1 rounded-full">{s.label}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

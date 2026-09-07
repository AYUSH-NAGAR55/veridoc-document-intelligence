import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, ClipboardCheck, Pencil, XCircle } from "lucide-react";
import { api } from "../api/client";
import { ConfidenceBadge, EmptyState, CardSkeleton } from "../components/shared";
import { useToast } from "../components/Toast";

function locationLabel(loc: any): string {
  if (!loc) return "—";
  if (loc.page) return `Page ${loc.page}`;
  if (loc.section) return loc.section;
  if (loc.sheet) return `Sheet ${loc.sheet}${loc.row ? `, Row ${loc.row}` : ""}`;
  if (loc.line) return `Line ${loc.line}`;
  return "—";
}

export default function ReviewQueue() {
  const [items, setItems] = useState<any[] | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [correction, setCorrection] = useState("");
  const toast = useToast();

  const load = () => api.listReviewQueue("pending").then(setItems);
  useEffect(() => { load(); }, []);

  const handle = async (action: "accept" | "correct" | "reject", id: string) => {
    try {
      if (action === "accept") await api.acceptReview(id);
      if (action === "reject") await api.rejectReview(id);
      if (action === "correct") {
        if (!correction.trim()) return toast.show("Enter a corrected value first.", "error");
        await api.correctReview(id, correction);
      }
      toast.show(`Item ${action === "correct" ? "corrected" : action + "ed"} and saved to verified knowledge.`, "success");
      setEditingId(null);
      setCorrection("");
      load();
    } catch (e: any) {
      toast.show(e.message, "error");
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-4xl">
      <h1 className="text-2xl font-semibold text-ink">Review Queue</h1>
      <p className="text-inkmuted text-sm mt-1 mb-6">Fields with low confidence or a failed validation check, waiting for a decision.</p>

      {items === null ? (
        <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)}</div>
      ) : items.length === 0 ? (
        <div className="bg-surface border border-line rounded-xl2">
          <EmptyState icon={<CheckCircle2 size={26} />} title="Everything is verified." description="You're all caught up." />
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <div key={item.id} className="bg-surface border border-line rounded-xl2 p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs text-inkmuted">Field</p>
                  <p className="font-medium text-ink">{item.field_name}</p>
                </div>
                <div>
                  <p className="text-xs text-inkmuted">AI Value</p>
                  <p className="font-medium text-ink">{item.ai_value}</p>
                </div>
                <div>
                  <p className="text-xs text-inkmuted">Confidence</p>
                  <ConfidenceBadge value={item.confidence} />
                </div>
                <div>
                  <p className="text-xs text-inkmuted">Source</p>
                  <p className="text-sm text-ink">{locationLabel(item.source_location)}</p>
                </div>
              </div>

              {item.evidence_text && (
                <p className="text-sm text-inkmuted bg-canvas rounded-lg p-3 mt-3">{item.evidence_text}</p>
              )}
              {item.validation_message && (
                <p className="text-sm text-peach-deep bg-peach-pastel rounded-lg p-3 mt-3">⚠ {item.validation_message}</p>
              )}

              <div className="flex items-center gap-2 mt-4">
                <button onClick={() => handle("accept", item.id)} className="flex items-center gap-1.5 text-sm bg-mint-pastel text-mint-deep px-3.5 py-2 rounded-lg font-medium">
                  <CheckCircle2 size={15} /> Accept
                </button>
                <button onClick={() => setEditingId(editingId === item.id ? null : item.id)} className="flex items-center gap-1.5 text-sm bg-blue-pastel text-blue-deep px-3.5 py-2 rounded-lg font-medium">
                  <Pencil size={15} /> Correct
                </button>
                <button onClick={() => handle("reject", item.id)} className="flex items-center gap-1.5 text-sm bg-danger-pastel text-danger-deep px-3.5 py-2 rounded-lg font-medium">
                  <XCircle size={15} /> Reject
                </button>
                <Link to={`/documents/${item.document_id}`} className="text-sm text-inkmuted ml-auto hover:text-ink">View document →</Link>
              </div>

              {editingId === item.id && (
                <div className="flex gap-2 mt-3">
                  <input
                    autoFocus
                    value={correction}
                    onChange={(e) => setCorrection(e.target.value)}
                    placeholder={`Corrected value for ${item.field_name}`}
                    className="flex-1 border border-line rounded-lg px-3 py-2 text-sm bg-canvas focus:border-blue-deep outline-none"
                  />
                  <button onClick={() => handle("correct", item.id)} className="bg-blue-deep text-white text-sm font-medium px-4 py-2 rounded-lg flex items-center gap-1.5">
                    <ClipboardCheck size={15} /> Save
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

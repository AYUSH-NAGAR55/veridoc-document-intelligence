import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import StatusBadge from "../components/StatusBadge";
import PipelineProgress from "../components/PipelineProgress";
import FieldCard from "../components/FieldCard";
import ReviewItem from "../components/ReviewItem";
import DocumentChat from "../components/DocumentChat";
import FileTypeIcon from "../components/FileTypeIcon";
import { api, locationLabel, PROCESSING_STATUSES } from "../lib/api";

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "review", label: "Review" },
  { key: "content", label: "Content" },
  { key: "ask", label: "Ask" },
];

export default function DocumentDetailPage() {
  const { id } = useParams();
  const [doc, setDoc] = useState(null);
  const [tab, setTab] = useState("overview");

  const refresh = useCallback(async () => {
    const fresh = await api.getDocument(id);
    setDoc(fresh);
    return fresh;
  }, [id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!doc || !PROCESSING_STATUSES.includes(doc.status)) return;
    const t = setInterval(refresh, 2000);
    return () => clearInterval(t);
  }, [doc, refresh]);

  useEffect(() => {
    if (doc?.status === "needs_review") setTab("review");
  }, [doc?.status]);

  async function handleAccept(fieldId) {
    await api.acceptField(fieldId);
    await refresh();
  }
  async function handleReject(fieldId) {
    await api.rejectField(fieldId);
    await refresh();
  }
  async function handleCorrect(fieldId, value) {
    await api.correctField(fieldId, value);
    await refresh();
  }

  if (!doc) {
    return <div className="max-w-4xl mx-auto px-8 py-10 text-ink-soft">Loading…</div>;
  }

  const pendingFields = doc.fields.filter((f) => f.status === "pending");
  const isProcessing = PROCESSING_STATUSES.includes(doc.status);
  const isReady = doc.status === "ready" || doc.status === "needs_review";

  return (
    <div className="max-w-4xl mx-auto px-8 py-10">
      <Link to="/documents" className="inline-flex items-center gap-1.5 text-sm text-ink-soft hover:text-ink mb-6">
        <ArrowLeft size={15} /> All documents
      </Link>

      <div className="flex items-start gap-4 mb-6">
        <FileTypeIcon fileType={doc.file_type} size={20} className="w-12 h-12" />
        <div className="min-w-0 flex-1">
          <h1 className="font-display text-2xl text-ink truncate">{doc.filename}</h1>
          <p className="text-sm text-ink-soft mt-1">
            {doc.doc_type !== "unknown" ? doc.doc_type.replace(/_/g, " ") : "Analyzing document type…"} · {doc.unit_count} {doc.unit_count_label}
          </p>
          {doc.summary && <p className="text-sm text-ink-soft mt-1 italic">{doc.summary}</p>}
        </div>
        <StatusBadge status={doc.status} />
      </div>

      {doc.status === "failed" && (
        <div className="rounded-xl2 border border-rose-soft bg-[#FDF6F5] p-5 mb-6 text-sm text-[#8A4A3D]">
          {doc.error_message?.split("\n")[0] || "Something went wrong while processing this document."}
        </div>
      )}

      {isProcessing ? (
        <PipelineProgress status={doc.status} />
      ) : (
        <>
          <div className="flex items-center gap-1 border-b border-border mb-6">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  tab === t.key ? "border-primary text-primary-deep" : "border-transparent text-ink-soft hover:text-ink"
                }`}
              >
                {t.label}
                {t.key === "review" && pendingFields.length > 0 && (
                  <span className="ml-1.5 inline-flex items-center justify-center w-4 h-4 rounded-full bg-amber-soft text-[#7A5326] text-[10px]">
                    {pendingFields.length}
                  </span>
                )}
              </button>
            ))}
          </div>

          {tab === "overview" && (
            <div className="space-y-3">
              {doc.fields.length === 0 ? (
                <p className="text-sm text-ink-soft py-8 text-center">
                  No structured fields were identified in this document — it's still fully searchable in the Ask tab.
                </p>
              ) : (
                doc.fields.map((f) => <FieldCard key={f.id} field={f} />)
              )}
            </div>
          )}

          {tab === "review" && (
            <div className="space-y-4">
              <AnimatePresence>
                {pendingFields.length === 0 ? (
                  <p className="text-sm text-ink-soft py-8 text-center">Nothing needs review — every field met the confidence bar.</p>
                ) : (
                  pendingFields.map((f) => (
                    <ReviewItem key={f.id} field={f} onAccept={handleAccept} onReject={handleReject} onCorrect={handleCorrect} />
                  ))
                )}
              </AnimatePresence>
            </div>
          )}

          {tab === "content" && (
            <div className="space-y-3">
              {doc.content_units.map((u) => (
                <div key={u.unit_index} className="rounded-xl2 border border-border bg-surface p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-ink">{locationLabel(u.location)} · {u.content_type}</p>
                    {u.ocr_confidence != null && (
                      <span className="text-xs text-ink-soft">OCR confidence {Math.round(u.ocr_confidence * 100)}%</span>
                    )}
                  </div>
                  <p className="text-xs text-ink-soft mt-1 line-clamp-2">{u.preview || "No extractable text in this section."}</p>
                </div>
              ))}
            </div>
          )}

          {tab === "ask" && isReady && <DocumentChat documentId={doc.id} />}
        </>
      )}
    </div>
  );
}

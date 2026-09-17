import { motion } from "framer-motion";
import { CheckCircle2, PencilLine, XCircle } from "lucide-react";
import ConfidenceRing from "./ConfidenceRing";
import { locationLabel } from "../lib/api";

const STATUS_LABEL = {
  auto_accepted: "Auto-accepted",
  accepted: "Accepted",
  corrected: "Corrected",
  rejected: "Rejected",
  pending: "Needs review",
};

export default function FieldCard({ field }) {
  const failedNotes = (field.validation_notes || []).filter((n) => !n.passed);
  const wasCorreted = field.status === "corrected" && field.original_ai_value !== field.field_value;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl2 border border-border bg-surface p-4 flex items-start gap-4"
    >
      <ConfidenceRing value={field.confidence} size={44} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-medium text-ink">{field.field_name}</p>
          <span className="text-[11px] text-ink-soft flex items-center gap-1">
            {field.status === "corrected" && <PencilLine size={12} />}
            {field.status === "rejected" && <XCircle size={12} className="text-[#8A4A3D]" />}
            {(field.status === "accepted" || field.status === "auto_accepted") && <CheckCircle2 size={12} className="text-sage" />}
            {STATUS_LABEL[field.status]}
          </span>
        </div>

        {wasCorreted ? (
          <div className="mt-1 space-y-0.5">
            <p className="text-xs text-ink-soft line-through decoration-[#D9A79C]">AI value: {field.original_ai_value}</p>
            <p className="font-mono text-base text-ink">{field.field_value} <span className="text-xs text-sage font-sans">verified</span></p>
          </div>
        ) : (
          <p className="font-mono text-base text-ink mt-1">{field.field_value || "—"}</p>
        )}

        <p className="text-xs text-ink-soft mt-1">Source: {locationLabel(field.location)}</p>

        {failedNotes.length > 0 && (
          <ul className="mt-2 space-y-0.5">
            {failedNotes.map((n, i) => (
              <li key={i} className="text-xs text-[#8A4A3D] flex gap-1">
                <span>⚠</span> {n.message}
              </li>
            ))}
          </ul>
        )}
      </div>
    </motion.div>
  );
}

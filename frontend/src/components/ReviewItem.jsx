import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Pencil, X, XCircle } from "lucide-react";
import ConfidenceRing from "./ConfidenceRing";
import { locationLabel } from "../lib/api";

export default function ReviewItem({ field, onAccept, onReject, onCorrect }) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(field.field_value);
  const [busy, setBusy] = useState(false);

  const arithmeticNote = (field.validation_notes || []).find((n) => n.rule === "arithmetic_check" && !n.passed);

  async function run(fn) {
    setBusy(true);
    try {
      await fn();
    } finally {
      setBusy(false);
    }
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97 }}
      className="rounded-xl2 border border-amber-soft bg-[#FEFBF6] p-5"
    >
      <div className="flex items-start gap-4">
        <ConfidenceRing value={field.confidence} size={48} />
        <div className="min-w-0 flex-1">
          <p className="text-xs uppercase tracking-wide text-[#7A5326] font-medium">Review required</p>
          <p className="font-medium text-ink mt-0.5">{field.field_name}</p>

          <p className="text-sm text-ink-soft mt-2">
            AI extracted: <span className="font-mono text-ink">{field.field_value}</span>
            {" · "}Source: {locationLabel(field.location)}
          </p>

          {arithmeticNote && (
            <p className="text-xs text-[#8A4A3D] mt-1.5">⚠ {arithmeticNote.message}</p>
          )}
          {field.source_snippet && (
            <p className="text-xs text-ink-soft mt-2 italic border-l-2 border-border pl-2">"…{field.source_snippet}…"</p>
          )}

          <AnimatePresence mode="wait">
            {editing ? (
              <motion.div key="edit" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-3 flex items-center gap-2">
                <input
                  autoFocus
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  className="flex-1 rounded-lg border border-border px-3 py-1.5 text-sm font-mono bg-surface focus:outline-none focus:ring-2 focus:ring-primary-soft"
                />
                <button
                  onClick={() => run(() => onCorrect(field.id, value)).then(() => setEditing(false))}
                  disabled={busy}
                  className="rounded-lg bg-primary text-white text-sm font-medium px-3 py-1.5 hover:bg-primary-deep transition-colors disabled:opacity-50"
                >
                  Save
                </button>
                <button onClick={() => setEditing(false)} className="text-ink-soft hover:text-ink">
                  <X size={16} />
                </button>
              </motion.div>
            ) : (
              <motion.div key="actions" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-3 flex items-center gap-2">
                <button
                  onClick={() => run(() => onAccept(field.id))}
                  disabled={busy}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-sage-soft text-[#3F6350] text-sm font-medium px-3 py-1.5 hover:brightness-95 transition disabled:opacity-50"
                >
                  <Check size={14} /> Accept
                </button>
                <button
                  onClick={() => setEditing(true)}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-border text-ink text-sm font-medium px-3 py-1.5 hover:bg-paper transition"
                >
                  <Pencil size={14} /> Correct
                </button>
                <button
                  onClick={() => run(() => onReject(field.id))}
                  disabled={busy}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-rose-soft text-[#8A4A3D] text-sm font-medium px-3 py-1.5 hover:bg-rose-soft/30 transition disabled:opacity-50"
                >
                  <XCircle size={14} /> Reject
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}

import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Trash2, Check } from "lucide-react";
import StatusBadge from "./StatusBadge";
import FileTypeIcon from "./FileTypeIcon";

function formatSize(bytes) {
  if (!bytes) return "";
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentCard({ doc, onDelete, selectMode, selected, onToggleSelect }) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={selectMode ? {} : { y: -3, rotateX: 2, rotateY: -2 }}
      style={{ transformStyle: "preserve-3d", perspective: 800 }}
      transition={{ type: "spring", stiffness: 300, damping: 24 }}
      className={`group relative rounded-xl2 border bg-surface p-5 shadow-soft hover:shadow-lift transition-shadow ${
        selected ? "border-primary ring-2 ring-primary-soft" : "border-border"
      }`}
    >
      {selectMode && (
        <button
          onClick={() => onToggleSelect(doc.id)}
          className={`absolute top-4 left-4 w-5 h-5 rounded-md border-2 flex items-center justify-center z-10 transition-colors ${
            selected ? "bg-primary border-primary" : "border-border bg-surface"
          }`}
        >
          {selected && <Check size={12} className="text-white" />}
        </button>
      )}
      <Link to={selectMode ? "#" : `/documents/${doc.id}`} onClick={(e) => selectMode && e.preventDefault()} className="block">
        <div className={`flex items-start gap-3 ${selectMode ? "pl-6" : ""}`}>
          <FileTypeIcon fileType={doc.file_type} size={18} className="w-10 h-10" />
          <div className="min-w-0 flex-1">
            <p className="font-medium text-ink truncate pr-6">{doc.filename}</p>
            <p className="text-xs text-ink-soft mt-0.5">
              {doc.doc_type !== "unknown" ? doc.doc_type.replace(/_/g, " ") : "Processing…"} · {doc.unit_count || "…"} {doc.unit_count_label}
              {doc.size_bytes ? ` · ${formatSize(doc.size_bytes)}` : ""}
            </p>
          </div>
        </div>
        <div className="mt-4 flex items-center justify-between">
          <StatusBadge status={doc.status} />
          <span className="text-[11px] text-ink-soft">
            {new Date(doc.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
          </span>
        </div>
      </Link>
      {!selectMode && (
        <button
          onClick={(e) => {
            e.preventDefault();
            onDelete(doc.id);
          }}
          className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity text-ink-soft hover:text-[#8A4A3D]"
          title="Delete document"
        >
          <Trash2 size={15} />
        </button>
      )}
    </motion.div>
  );
}

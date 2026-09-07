import { Link } from "react-router-dom";
import { FileText, FileSpreadsheet, FileJson, Image as ImageIcon, File } from "lucide-react";
import { StatusPill } from "./shared";
import { formatBytes, formatDate } from "../lib/format";

const ICONS: Record<string, any> = {
  pdf: FileText,
  docx: FileText,
  csv: FileSpreadsheet,
  json: FileJson,
  image: ImageIcon,
  txt: File,
};

export function DocumentCard({
  doc,
  selected,
  onToggleSelect,
}: {
  doc: any;
  selected?: boolean;
  onToggleSelect?: (id: string) => void;
}) {
  const Icon = ICONS[doc.file_type] || File;
  return (
    <div className="relative bg-surface border border-line rounded-xl2 p-5 hover:shadow-card transition-shadow">
      {onToggleSelect && (
        <input
          type="checkbox"
          checked={!!selected}
          onChange={() => onToggleSelect(doc.id)}
          className="absolute top-4 right-4 h-4 w-4 accent-blue-deep"
          aria-label={`Select ${doc.filename}`}
        />
      )}
      <Link to={`/documents/${doc.id}`} className="block">
        <div className="flex items-start gap-3">
          <div className="h-10 w-10 rounded-lg bg-blue-pastel flex items-center justify-center text-blue-deep shrink-0">
            <Icon size={18} />
          </div>
          <div className="min-w-0">
            <p className="font-medium text-ink truncate pr-6">{doc.filename}</p>
            <p className="text-xs text-inkmuted mt-0.5">
              {formatBytes(doc.size_bytes)} • {formatDate(doc.created_at)}
            </p>
          </div>
        </div>
        <div className="flex items-center justify-between mt-4">
          <StatusPill status={doc.status} />
          {doc.quality_score != null && (
            <span className="text-xs font-mono text-inkmuted">{doc.quality_score}/100</span>
          )}
        </div>
        {doc.duplicate_of && (
          <p className="text-xs text-peach-deep mt-2">⚠ Possible duplicate detected</p>
        )}
      </Link>
    </div>
  );
}

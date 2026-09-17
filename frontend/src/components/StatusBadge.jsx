import { Loader2, CheckCircle2, AlertTriangle, XCircle, Clock } from "lucide-react";
import { PROCESSING_STATUSES, STATUS_LABELS } from "../lib/api";

const STYLES = {
  ready: { bg: "bg-sage-soft", text: "text-[#3F6350]", icon: CheckCircle2 },
  needs_review: { bg: "bg-amber-soft", text: "text-[#7A5326]", icon: AlertTriangle },
  failed: { bg: "bg-rose-soft", text: "text-[#8A4A3D]", icon: XCircle },
  uploaded: { bg: "bg-primary-soft", text: "text-primary-deep", icon: Clock },
};

export default function StatusBadge({ status }) {
  const isProcessing = PROCESSING_STATUSES.includes(status);
  const style = STYLES[status] || { bg: "bg-primary-soft", text: "text-primary-deep", icon: Loader2 };
  const Icon = isProcessing ? Loader2 : style.icon;

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${style.bg} ${style.text}`}>
      <Icon size={13} className={isProcessing ? "animate-spin" : ""} />
      {STATUS_LABELS[status] || status}
    </span>
  );
}

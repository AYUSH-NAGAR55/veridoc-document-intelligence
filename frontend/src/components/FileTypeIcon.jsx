import { FileText, FileSpreadsheet, FileJson, FileImage, File, Table2 } from "lucide-react";

const TYPE_CONFIG = {
  pdf: { icon: FileText, bg: "bg-rose-soft", fg: "text-[#8A4A3D]" },
  docx: { icon: FileText, bg: "bg-primary-soft", fg: "text-primary-deep" },
  txt: { icon: File, bg: "bg-[#E9E5DC]", fg: "text-ink-soft" },
  csv: { icon: Table2, bg: "bg-sage-soft", fg: "text-[#3F6350]" },
  xlsx: { icon: FileSpreadsheet, bg: "bg-sage-soft", fg: "text-[#3F6350]" },
  xls: { icon: FileSpreadsheet, bg: "bg-sage-soft", fg: "text-[#3F6350]" },
  json: { icon: FileJson, bg: "bg-amber-soft", fg: "text-[#7A5326]" },
  png: { icon: FileImage, bg: "bg-[#E3DCF0]", fg: "text-[#5F4A8A]" },
  jpg: { icon: FileImage, bg: "bg-[#E3DCF0]", fg: "text-[#5F4A8A]" },
  jpeg: { icon: FileImage, bg: "bg-[#E3DCF0]", fg: "text-[#5F4A8A]" },
};

export default function FileTypeIcon({ fileType, size = 18, className = "" }) {
  const config = TYPE_CONFIG[fileType?.toLowerCase()] || { icon: File, bg: "bg-[#E9E5DC]", fg: "text-ink-soft" };
  const Icon = config.icon;
  return (
    <div className={`rounded-xl flex items-center justify-center shrink-0 ${config.bg} ${className}`}>
      <Icon size={size} className={config.fg} />
    </div>
  );
}

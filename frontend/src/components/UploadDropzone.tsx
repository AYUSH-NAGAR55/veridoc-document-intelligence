import { useCallback, useRef, useState } from "react";
import { UploadCloud, FileText } from "lucide-react";
import clsx from "clsx";
import { api } from "../api/client";
import { useToast } from "./Toast";

const ACCEPTED = ".pdf,.docx,.txt,.csv,.json,.png,.jpg,.jpeg";

export function UploadDropzone({ onUploaded }: { onUploaded: (doc: { id: string; filename: string }) => void }) {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];
      setUploading(true);
      try {
        const result = await api.uploadDocument(file);
        toast.show(`${file.name} uploaded — processing has started.`, "success");
        onUploaded(result);
      } catch (err: any) {
        toast.show(err.message || "Upload failed.", "error");
      } finally {
        setUploading(false);
      }
    },
    [onUploaded, toast]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFiles(e.dataTransfer.files);
      }}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
      className={clsx(
        "border-2 border-dashed rounded-xl2 p-10 text-center cursor-pointer transition-colors",
        dragOver ? "border-blue-deep bg-blue-pastel/40" : "border-line bg-surface hover:border-blue-deep/60"
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <div className="flex flex-col items-center gap-3">
        <div className="h-12 w-12 rounded-full bg-blue-pastel flex items-center justify-center text-blue-deep">
          {uploading ? <FileText size={22} className="animate-pulse" /> : <UploadCloud size={22} />}
        </div>
        <p className="font-medium text-ink">{uploading ? "Uploading..." : "Drop a document here, or click to browse"}</p>
        <p className="text-sm text-inkmuted">PDF, DOCX, TXT, CSV, JSON, PNG, JPG — up to 25MB</p>
      </div>
    </div>
  );
}

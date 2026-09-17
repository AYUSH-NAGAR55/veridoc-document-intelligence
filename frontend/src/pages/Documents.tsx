import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search, Trash2, FileStack, X } from "lucide-react";
import { api } from "../api/client";
import { UploadDropzone } from "../components/UploadDropzone";
import { DocumentCard } from "../components/DocumentCard";
import { CardSkeleton, EmptyState } from "../components/shared";
import { useToast } from "../components/Toast";

const STATUS_OPTIONS = ["all", "ready", "uploaded", "understanding", "extracting", "validating", "verifying", "indexing", "failed"];

export default function Documents() {
  const [params, setParams] = useSearchParams();
  const [docs, setDocs] = useState<any[] | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [showUpload, setShowUpload] = useState(params.get("upload") === "1");
  const [selected, setSelected] = useState<string[]>([]);
  const toast = useToast();

  const load = () => {
    api.listDocuments({ search: search || undefined, status: status === "all" ? undefined : status }).then(setDocs);
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 4000); // poll for processing status updates
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, status]);

  const toggleSelect = (id: string) => setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  const deleteSelected = async () => {
    if (!confirm(`Delete ${selected.length} document(s)? This cannot be undone.`)) return;
    await api.deleteDocuments(selected);
    toast.show(`Deleted ${selected.length} document(s).`, "success");
    setSelected([]);
    load();
  };

  return (
    <div className="p-6 md:p-8 max-w-6xl">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-ink">Documents</h1>
          <p className="text-inkmuted text-sm mt-1">Upload, inspect, and manage your document knowledge base.</p>
        </div>
        <button
          onClick={() => {
            setShowUpload((v) => !v);
            setParams({});
          }}
          className="bg-brand-deep text-white text-sm font-medium px-4 py-2.5 rounded-lg hover:bg-brand-deep/90 transition-colors"
        >
          {showUpload ? "Close" : "Upload a document"}
        </button>
      </div>

      {showUpload && (
        <div className="mb-6">
          <UploadDropzone onUploaded={() => { load(); }} />
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-inkmuted" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by filename..."
            className="w-full pl-9 pr-3 py-2.5 border border-line rounded-lg bg-surface text-sm focus:border-brand-deep outline-none"
          />
        </div>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="border border-line rounded-lg bg-surface text-sm px-3 py-2.5 focus:border-brand-deep outline-none"
        >
          {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s === "all" ? "All statuses" : s}</option>)}
        </select>
        {selected.length > 0 && (
          <button onClick={deleteSelected} className="flex items-center gap-1.5 text-sm text-danger-deep border border-danger-deep/30 bg-danger-pastel px-3 py-2.5 rounded-lg">
            <Trash2 size={15} /> Delete {selected.length} selected
          </button>
        )}
      </div>

      {docs === null ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : docs.length === 0 ? (
        <div className="bg-surface border border-line rounded-xl2">
          {search || status !== "all" ? (
            <EmptyState icon={<X size={26} />} title="Nothing matched your search." description="Try a different filename or status filter." />
          ) : (
            <EmptyState
              icon={<FileStack size={26} />}
              title="No documents yet."
              description="Upload your first document to create verified knowledge."
              action={<button onClick={() => setShowUpload(true)} className="bg-brand-deep text-white text-sm font-medium px-4 py-2.5 rounded-lg">Upload a document</button>}
            />
          )}
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {docs.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} selected={selected.includes(doc.id)} onToggleSelect={toggleSelect} />
          ))}
        </div>
      )}
    </div>
  );
}

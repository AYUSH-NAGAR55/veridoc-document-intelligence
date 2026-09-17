import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Trash2, X } from "lucide-react";
import UploadDropzone from "../components/UploadDropzone";
import DocumentCard from "../components/DocumentCard";
import { api, PROCESSING_STATUSES } from "../lib/api";

export default function DocumentsPage({ documents, setDocuments }) {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [selectMode, setSelectMode] = useState(false);
  const [selected, setSelected] = useState(new Set());
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    const hasProcessing = documents.some((d) => PROCESSING_STATUSES.includes(d.status));
    if (!hasProcessing) return;
    const t = setInterval(async () => {
      const fresh = await api.listDocuments();
      setDocuments(fresh);
    }, 2500);
    return () => clearInterval(t);
  }, [documents, setDocuments]);

  useEffect(() => {
    const t = setTimeout(() => {
      api.listDocuments(search).then(setDocuments);
    }, 250);
    return () => clearTimeout(t);
  }, [search]);

  async function handleUpload(file) {
    const doc = await api.uploadDocument(file);
    setDocuments((prev) => [doc, ...prev]);
    navigate(`/documents/${doc.id}`);
  }

  async function handleDelete(id) {
    await api.deleteDocument(id);
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  }

  function toggleSelect(id) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function toggleSelectAll() {
    setSelected((prev) => (prev.size === documents.length ? new Set() : new Set(documents.map((d) => d.id))));
  }

  async function handleBulkDelete() {
    await api.bulkDeleteDocuments(Array.from(selected));
    setDocuments((prev) => prev.filter((d) => !selected.has(d.id)));
    setSelected(new Set());
    setSelectMode(false);
    setConfirming(false);
  }

  return (
    <div className="max-w-5xl mx-auto px-8 py-10">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-ink">Documents</h1>
          <p className="text-ink-soft mt-1.5">
            Upload PDF, Word, Excel, CSV, JSON, text, or image files — VeriDoc understands and verifies each before it becomes searchable.
          </p>
        </div>
        <button
          onClick={() => {
            setSelectMode((s) => !s);
            setSelected(new Set());
          }}
          className={`shrink-0 text-sm font-medium px-3 py-2 rounded-xl2 border transition-colors ${
            selectMode ? "bg-primary-soft border-primary text-primary-deep" : "border-border text-ink-soft hover:bg-surface"
          }`}
        >
          {selectMode ? "Cancel" : "Select"}
        </button>
      </div>

      <div className="mb-6">
        <UploadDropzone onUpload={handleUpload} />
      </div>

      <div className="flex items-center gap-3 mb-5">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-soft" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents…"
            className="w-full rounded-xl2 border border-border bg-surface pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-soft"
          />
        </div>
        {selectMode && documents.length > 0 && (
          <button onClick={toggleSelectAll} className="text-xs text-primary-deep hover:underline shrink-0">
            {selected.size === documents.length ? "Deselect all" : "Select all"}
          </button>
        )}
      </div>

      {documents.length === 0 ? (
        <div className="text-center py-16 text-ink-soft text-sm">No documents found.</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {documents.map((doc) => (
            <DocumentCard
              key={doc.id}
              doc={doc}
              onDelete={handleDelete}
              selectMode={selectMode}
              selected={selected.has(doc.id)}
              onToggleSelect={toggleSelect}
            />
          ))}
        </div>
      )}

      <AnimatePresence>
        {selectMode && selected.size > 0 && (
          <motion.div
            initial={{ y: 60, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 60, opacity: 0 }}
            className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-ink text-white rounded-xl2 shadow-lift px-5 py-3 flex items-center gap-4"
          >
            <span className="text-sm">{selected.size} selected</span>
            <button
              onClick={() => setConfirming(true)}
              className="inline-flex items-center gap-1.5 text-sm font-medium bg-[#8A4A3D] px-3 py-1.5 rounded-lg hover:brightness-110 transition"
            >
              <Trash2 size={14} /> Delete
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {confirming && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/30 flex items-center justify-center z-50"
            onClick={() => setConfirming(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-surface rounded-xl2 shadow-lift p-6 max-w-sm w-full mx-4"
            >
              <div className="flex items-start justify-between">
                <h3 className="font-medium text-ink">Delete {selected.size} document{selected.size !== 1 ? "s" : ""}?</h3>
                <button onClick={() => setConfirming(false)}><X size={16} className="text-ink-soft" /></button>
              </div>
              <p className="text-sm text-ink-soft mt-2">
                This permanently removes the file{selected.size !== 1 ? "s" : ""}, extracted data, review history, and search index entries. This can't be undone.
              </p>
              <div className="mt-5 flex justify-end gap-2">
                <button onClick={() => setConfirming(false)} className="text-sm px-3 py-2 rounded-lg text-ink-soft hover:bg-paper">
                  Cancel
                </button>
                <button
                  onClick={handleBulkDelete}
                  className="text-sm px-3 py-2 rounded-lg bg-[#8A4A3D] text-white font-medium hover:brightness-110"
                >
                  Delete permanently
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

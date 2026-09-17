const BASE = "/api";

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  listDocuments: (search) => fetch(`${BASE}/documents${search ? `?search=${encodeURIComponent(search)}` : ""}`).then(handle),
  getDocument: (id) => fetch(`${BASE}/documents/${id}`).then(handle),
  uploadDocument: (file) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/documents`, { method: "POST", body: form }).then(handle);
  },
  deleteDocument: (id) => fetch(`${BASE}/documents/${id}`, { method: "DELETE" }).then(handle),
  bulkDeleteDocuments: (ids) =>
    fetch(`${BASE}/documents/bulk-delete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_ids: ids }),
    }).then(handle),
  getReviewQueue: () => fetch(`${BASE}/review`).then(handle),
  acceptField: (fieldId) => fetch(`${BASE}/review/${fieldId}/accept`, { method: "POST" }).then(handle),
  rejectField: (fieldId, reason) =>
    fetch(`${BASE}/review/${fieldId}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason: reason || null }),
    }).then(handle),
  correctField: (fieldId, correctedValue) =>
    fetch(`${BASE}/review/${fieldId}/correct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ corrected_value: correctedValue }),
    }).then(handle),
  ask: (documentId, question) =>
    fetch(`${BASE}/documents/${documentId}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }).then(handle),
  getDashboard: () => fetch(`${BASE}/dashboard`).then(handle),
};

export const PROCESSING_STATUSES = ["uploaded", "understanding", "extracting", "validating", "verifying", "indexing"];

export const STATUS_LABELS = {
  uploaded: "Queued",
  understanding: "Understanding",
  extracting: "Extracting content",
  validating: "Validating",
  verifying: "Verifying",
  indexing: "Building knowledge base",
  ready: "Ready",
  needs_review: "Needs review",
  failed: "Failed",
};

export function locationLabel(location) {
  if (!location) return "Document";
  const parts = [];
  if (location.page != null) parts.push(`Page ${location.page}`);
  if (location.sheet != null) parts.push(`Sheet ${location.sheet}`);
  if (location.row != null) parts.push(`Row ${location.row}`);
  if (location.column != null) parts.push(`Column ${location.column}`);
  if (location.section != null) parts.push(location.section);
  if (location.paragraph != null) parts.push(`Paragraph ${location.paragraph}`);
  if (location.table != null) parts.push(`Table ${location.table}`);
  if (location.line != null) parts.push(`Line ${location.line}`);
  if (location.image != null) parts.push(`Image ${location.image}`);
  return parts.length ? parts.join(", ") : "Document";
}

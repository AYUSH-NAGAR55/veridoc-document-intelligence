const BASE_URL = import.meta.env.VITE_API_URL || "/api";

// Every browser gets its own unguessable random ID on first load, persisted in
// localStorage, and sent as X-User-Id on every request. The backend uses this
// to keep each user's documents, queries, and results completely isolated -
// see backend/app/api/deps.py for the server-side enforcement.
function getOwnerId(): string {
  const KEY = "veridoc_owner_id";
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(KEY, id);
  }
  return id;
}

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      "X-User-Id": getOwnerId(),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = "Something went wrong. Please try again.";
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(detail, res.status);
  }
  if (res.status === 204) return undefined as T;
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return res.json();
  return res.blob() as unknown as T;
}

export const api = {
  health: () => request<{ status: string; llm_provider: string; database: string }>("/health"),

  listDocuments: (params?: { search?: string; file_type?: string; status?: string }) => {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    return request<any[]>(`/documents${qs ? `?${qs}` : ""}`);
  },
  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ id: string; filename: string; status: string }>("/documents/upload", {
      method: "POST",
      body: form,
    });
  },
  getDocument: (id: string) => request<any>(`/documents/${id}`),
  deleteDocument: (id: string) => request<any>(`/documents/${id}`, { method: "DELETE" }),
  deleteDocuments: (ids: string[]) =>
    request<any>(`/documents/delete-batch`, { method: "POST", body: JSON.stringify(ids) }),
  getDocumentContent: (id: string) => request<any[]>(`/documents/${id}/content`),
  getExtractions: (id: string) => request<any>(`/documents/${id}/extractions`),
  getValidation: (id: string) => request<any[]>(`/documents/${id}/validation`),
  getAudit: (id: string) => request<any[]>(`/documents/${id}/audit`),
  getAnomalies: (id: string) => request<any[]>(`/documents/${id}/anomalies`),
  exportDocument: async (id: string, format: "json" | "csv" | "xlsx", filename: string) => {
    // Plain <a href> downloads can't carry the X-User-Id header, and this
    // endpoint is owner-scoped like everything else - so exports are fetched
    // here (with the header) and saved via a Blob instead of a direct link.
    const res = await fetch(`${BASE_URL}/documents/${id}/export?format=${format}`, {
      headers: { "X-User-Id": getOwnerId() },
    });
    if (!res.ok) {
      let detail = "Export failed.";
      try { detail = (await res.json()).detail || detail; } catch { /* ignore */ }
      throw new ApiError(detail, res.status);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filename}_verified.${format}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },

  listReviewQueue: (status = "pending") => request<any[]>(`/review-queue?status=${status}`),
  acceptReview: (id: string, reviewer_note?: string) =>
    request<any>(`/review-queue/${id}/accept`, { method: "POST", body: JSON.stringify({ reviewer_note }) }),
  correctReview: (id: string, corrected_value: string, reviewer_note?: string) =>
    request<any>(`/review-queue/${id}/correct`, {
      method: "POST",
      body: JSON.stringify({ corrected_value, reviewer_note }),
    }),
  rejectReview: (id: string, reviewer_note?: string) =>
    request<any>(`/review-queue/${id}/reject`, { method: "POST", body: JSON.stringify({ reviewer_note }) }),

  query: (question: string, document_ids?: string[]) =>
    request<any>(`/query`, { method: "POST", body: JSON.stringify({ question, document_ids, top_k: 5 }) }),

  compareDocuments: (document_id_a: string, document_id_b: string) =>
    request<any>(`/documents/compare`, { method: "POST", body: JSON.stringify({ document_id_a, document_id_b }) }),

  analytics: () => request<any>(`/analytics`),
};

export { ApiError };

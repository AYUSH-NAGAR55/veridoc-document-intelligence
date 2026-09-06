const BASE_URL = import.meta.env.VITE_API_URL || "/api";

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
  exportDocument: (id: string, format: "json" | "csv") => `${BASE_URL}/documents/${id}/export?format=${format}`,

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

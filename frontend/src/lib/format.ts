export function formatConfidence(value: number): string {
  return `${Math.round((value <= 1 ? value * 100 : value))}%`;
}

export function confidenceTone(value: number): "high" | "medium" | "low" {
  const pct = value <= 1 ? value * 100 : value;
  if (pct >= 85) return "high";
  if (pct >= 70) return "medium";
  return "low";
}

export function formatDate(iso?: string | null): string {
  if (!iso) return "—";
  const date = new Date(iso);
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function formatBytes(bytes: number): string {
  if (!bytes) return "0 KB";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  let value = bytes;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i++;
  }
  return `${value.toFixed(value < 10 && i > 0 ? 1 : 0)} ${units[i]}`;
}

export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    uploaded: "Uploaded",
    understanding: "Understanding",
    extracting: "Extracting",
    validating: "Validating",
    verifying: "Verifying",
    indexing: "Indexing",
    ready: "Ready",
    failed: "Failed",
  };
  return map[status] || status;
}

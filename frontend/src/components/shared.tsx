import React from "react";
import clsx from "clsx";
import { formatConfidence, confidenceTone, statusLabel } from "../lib/format";

export function EmptyState({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center text-center py-16 px-6">
      {icon && <div className="mb-4 text-blue-deep">{icon}</div>}
      <h3 className="text-lg font-semibold text-ink">{title}</h3>
      <p className="text-inkmuted text-sm mt-1.5 max-w-sm">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx("animate-pulse rounded-lg bg-line/70", className)} />;
}

export function CardSkeleton() {
  return (
    <div className="bg-surface border border-line rounded-xl2 p-5 space-y-3">
      <Skeleton className="h-4 w-2/3" />
      <Skeleton className="h-3 w-1/2" />
      <Skeleton className="h-3 w-1/3" />
    </div>
  );
}

export function ConfidenceBadge({ value }: { value: number }) {
  const tone = confidenceTone(value);
  const styles = {
    high: "bg-mint-pastel text-mint-deep",
    medium: "bg-peach-pastel text-peach-deep",
    low: "bg-danger-pastel text-danger-deep",
  }[tone];
  return (
    <span className={clsx("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-mono font-medium", styles)}>
      {formatConfidence(value)}
    </span>
  );
}

export function StatusPill({ status }: { status: string }) {
  const styles: Record<string, string> = {
    ready: "bg-mint-pastel text-mint-deep",
    failed: "bg-danger-pastel text-danger-deep",
    uploaded: "bg-blue-pastel text-blue-deep",
    understanding: "bg-blue-pastel text-blue-deep",
    extracting: "bg-lavender-pastel text-lavender-deep",
    validating: "bg-lavender-pastel text-lavender-deep",
    verifying: "bg-peach-pastel text-peach-deep",
    indexing: "bg-peach-pastel text-peach-deep",
  };
  return (
    <span className={clsx("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", styles[status] || "bg-line text-inkmuted")}>
      {statusLabel(status)}
    </span>
  );
}

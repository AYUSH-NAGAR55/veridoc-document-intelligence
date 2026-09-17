import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FileStack, ShieldCheck, ListChecks, XCircle, Gauge, AlertTriangle } from "lucide-react";
import { api } from "../api/client";
import { CardSkeleton, EmptyState, StatusPill } from "../components/shared";
import { formatDate } from "../lib/format";

type MetricCard = { key: string; label: string; icon: any; tone: string; isPercent?: boolean };

const METRIC_CARDS: MetricCard[] = [
  { key: "documents_processed", label: "Documents Processed", icon: FileStack, tone: "blue" },
  { key: "verified_documents", label: "Verified Documents", icon: ShieldCheck, tone: "mint" },
  { key: "pending_reviews", label: "Pending Reviews", icon: ListChecks, tone: "peach" },
  { key: "rejected_items", label: "Rejected Items", icon: XCircle, tone: "danger" },
  { key: "average_confidence", label: "Average Confidence", icon: Gauge, tone: "blue", isPercent: true },
  { key: "validation_issues", label: "Validation Issues", icon: AlertTriangle, tone: "peach" },
];

const TONE_CLASSES: Record<string, string> = {
  blue: "bg-brand-pastel text-brand-deep",
  mint: "bg-mint-pastel text-mint-deep",
  peach: "bg-peach-pastel text-peach-deep",
  danger: "bg-danger-pastel text-danger-deep",
};

export default function Dashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.analytics().then(setData).finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 md:p-8 max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-ink">Dashboard</h1>
          <p className="text-inkmuted text-sm mt-1">An overview of your verified document knowledge.</p>
        </div>
        <Link to="/documents?upload=1" className="bg-brand-deep text-white text-sm font-medium px-4 py-2.5 rounded-lg hover:bg-brand-deep/90 transition-colors">
          Upload a document
        </Link>
      </div>

      {loading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      ) : !data || data.documents_processed === 0 ? (
        <div className="bg-surface border border-line rounded-xl2">
          <EmptyState
            icon={<FileStack size={28} />}
            title="No documents yet."
            description="Upload your first document to create verified knowledge."
            action={
              <Link to="/documents?upload=1" className="bg-brand-deep text-white text-sm font-medium px-4 py-2.5 rounded-lg">
                Upload a document
              </Link>
            }
          />
        </div>
      ) : (
        <>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {METRIC_CARDS.map(({ key, label, icon: Icon, tone, isPercent }) => {
              const raw = data[key] ?? 0;
              const value = isPercent ? `${Math.round(raw * 100)}%` : raw;
              return (
                <div key={key} className="bg-surface border border-line rounded-xl2 p-5">
                  <div className={`h-9 w-9 rounded-lg flex items-center justify-center mb-3 ${TONE_CLASSES[tone]}`}>
                    <Icon size={16} />
                  </div>
                  <p className="text-2xl font-semibold text-ink font-mono">{value}</p>
                  <p className="text-sm text-inkmuted mt-1">{label}</p>
                </div>
              );
            })}
          </div>

          <div className="grid lg:grid-cols-2 gap-6 mt-8">
            <div className="bg-surface border border-line rounded-xl2 p-5">
              <h2 className="font-semibold text-ink mb-4">Recent documents</h2>
              <div className="space-y-2">
                {data.recent_documents.map((d: any) => (
                  <Link key={d.id} to={`/documents/${d.id}`} className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-canvas transition-colors">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-ink truncate">{d.filename}</p>
                      <p className="text-xs text-inkmuted">{formatDate(d.created_at)}</p>
                    </div>
                    <StatusPill status={d.status} />
                  </Link>
                ))}
              </div>
            </div>

            <div className="bg-surface border border-line rounded-xl2 p-5">
              <h2 className="font-semibold text-ink mb-4">Recent review activity</h2>
              {data.recent_queries.length === 0 ? (
                <p className="text-sm text-inkmuted">No queries asked yet.</p>
              ) : (
                <div className="space-y-3">
                  {data.recent_queries.map((q: any) => (
                    <div key={q.id} className="py-2 px-3 rounded-lg hover:bg-canvas transition-colors">
                      <p className="text-sm font-medium text-ink">{q.question}</p>
                      <p className="text-xs text-inkmuted mt-0.5 line-clamp-1">{q.answer}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

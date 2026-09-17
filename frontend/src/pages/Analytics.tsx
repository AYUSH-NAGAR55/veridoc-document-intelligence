import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { api } from "../api/client";
import { Skeleton } from "../components/shared";

const COLORS = ["#B45309", "#7C6FE0", "#1F9C77", "#E0794A", "#D64545", "#5B6470"];

export default function Analytics() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    api.analytics().then(setData);
  }, []);

  if (!data) {
    return (
      <div className="p-8 max-w-4xl space-y-4">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const byType = Object.entries(data.documents_by_type).map(([name, value]) => ({ name: name.toUpperCase(), value }));

  return (
    <div className="p-6 md:p-8 max-w-5xl">
      <h1 className="text-2xl font-semibold text-ink mb-6">Analytics</h1>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-surface border border-line rounded-xl2 p-5">
          <h2 className="font-semibold text-ink mb-4">Documents by type</h2>
          {byType.length === 0 ? (
            <p className="text-sm text-inkmuted">No documents processed yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={byType} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={3}>
                  {byType.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-surface border border-line rounded-xl2 p-5">
          <h2 className="font-semibold text-ink mb-4">Summary</h2>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between"><dt className="text-inkmuted">Documents processed</dt><dd className="font-mono font-medium">{data.documents_processed}</dd></div>
            <div className="flex justify-between"><dt className="text-inkmuted">Verified documents</dt><dd className="font-mono font-medium">{data.verified_documents}</dd></div>
            <div className="flex justify-between"><dt className="text-inkmuted">Pending reviews</dt><dd className="font-mono font-medium">{data.pending_reviews}</dd></div>
            <div className="flex justify-between"><dt className="text-inkmuted">Rejected items</dt><dd className="font-mono font-medium">{data.rejected_items}</dd></div>
            <div className="flex justify-between"><dt className="text-inkmuted">Average confidence</dt><dd className="font-mono font-medium">{Math.round(data.average_confidence * 100)}%</dd></div>
            <div className="flex justify-between"><dt className="text-inkmuted">Validation issues</dt><dd className="font-mono font-medium">{data.validation_issues}</dd></div>
          </dl>
        </div>
      </div>

      <div className="bg-surface border border-line rounded-xl2 p-5 mt-6">
        <h2 className="font-semibold text-ink mb-4">Recent queries</h2>
        {data.recent_queries.length === 0 ? (
          <p className="text-sm text-inkmuted">No queries asked yet.</p>
        ) : (
          <div className="divide-y divide-line">
            {data.recent_queries.map((q: any) => (
              <div key={q.id} className="py-3">
                <p className="text-sm font-medium text-ink">{q.question}</p>
                <p className="text-xs text-inkmuted mt-1">{q.grounded ? `Confidence ${Math.round((q.confidence || 0) * 100)}%` : "Not found in documents"}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

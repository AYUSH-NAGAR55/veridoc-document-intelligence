import { useEffect, useState } from "react";
import { GitCompareArrows } from "lucide-react";
import { api } from "../api/client";
import { EmptyState } from "../components/shared";
import { useToast } from "../components/Toast";

export default function Compare() {
  const [docs, setDocs] = useState<any[]>([]);
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  useEffect(() => {
    api.listDocuments({ status: "ready" }).then(setDocs);
  }, []);

  const runCompare = async () => {
    if (!a || !b || a === b) return toast.show("Select two different documents.", "error");
    setLoading(true);
    try {
      setResult(await api.compareDocuments(a, b));
    } catch (e: any) {
      toast.show(e.message, "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-4xl">
      <h1 className="text-2xl font-semibold text-ink">Compare Documents</h1>
      <p className="text-inkmuted text-sm mt-1 mb-6">See what changed between two verified documents.</p>

      {docs.length < 2 ? (
        <div className="bg-surface border border-line rounded-xl2">
          <EmptyState icon={<GitCompareArrows size={26} />} title="Need at least two ready documents." description="Upload and process another document to enable comparison." />
        </div>
      ) : (
        <>
          <div className="grid sm:grid-cols-2 gap-4 mb-5">
            <select value={a} onChange={(e) => setA(e.target.value)} className="border border-line rounded-lg px-3.5 py-2.5 bg-surface text-sm">
              <option value="">Select document A</option>
              {docs.map((d) => <option key={d.id} value={d.id}>{d.filename}</option>)}
            </select>
            <select value={b} onChange={(e) => setB(e.target.value)} className="border border-line rounded-lg px-3.5 py-2.5 bg-surface text-sm">
              <option value="">Select document B</option>
              {docs.map((d) => <option key={d.id} value={d.id}>{d.filename}</option>)}
            </select>
          </div>
          <button onClick={runCompare} disabled={loading} className="bg-blue-deep text-white text-sm font-medium px-5 py-2.5 rounded-lg disabled:opacity-60">
            {loading ? "Comparing..." : "Compare"}
          </button>

          {result && (
            <div className="mt-8 space-y-6">
              {result.changed.length > 0 && (
                <div>
                  <h3 className="font-semibold text-ink mb-3">Changed values</h3>
                  <div className="space-y-2">
                    {result.changed.map((c: any, i: number) => (
                      <div key={i} className="bg-surface border border-line rounded-xl2 p-4 flex items-center justify-between flex-wrap gap-2">
                        <p className="font-medium text-ink">{c.field_name}</p>
                        <div className="text-sm text-inkmuted">
                          {c.value_a} <span className="mx-1">→</span> <span className="text-ink font-medium">{c.value_b}</span>
                        </div>
                        {c.percent_change != null && (
                          <span className={`text-xs font-mono px-2 py-0.5 rounded-full ${c.percent_change >= 0 ? "bg-mint-pastel text-mint-deep" : "bg-danger-pastel text-danger-deep"}`}>
                            {c.percent_change >= 0 ? "+" : ""}{c.percent_change}%
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {result.added.length > 0 && (
                <div>
                  <h3 className="font-semibold text-ink mb-3">Added in document B</h3>
                  <div className="space-y-2">
                    {result.added.map((c: any, i: number) => (
                      <div key={i} className="bg-mint-pastel text-mint-deep rounded-xl2 p-4 text-sm"><b>{c.field_name}:</b> {c.value_b}</div>
                    ))}
                  </div>
                </div>
              )}
              {result.removed.length > 0 && (
                <div>
                  <h3 className="font-semibold text-ink mb-3">Removed from document B</h3>
                  <div className="space-y-2">
                    {result.removed.map((c: any, i: number) => (
                      <div key={i} className="bg-danger-pastel text-danger-deep rounded-xl2 p-4 text-sm"><b>{c.field_name}:</b> {c.value_a}</div>
                    ))}
                  </div>
                </div>
              )}
              {result.changed.length === 0 && result.added.length === 0 && result.removed.length === 0 && (
                <p className="text-sm text-inkmuted">No differences found in verified values between these documents.</p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

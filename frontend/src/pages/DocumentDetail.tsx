import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Download, Trash2, AlertTriangle, CheckCircle2, Sparkles } from "lucide-react";
import { api } from "../api/client";
import { StatusPill, ConfidenceBadge, Skeleton, EmptyState } from "../components/shared";
import { PipelineProgress } from "../components/PipelineProgress";
import { formatBytes, formatDate } from "../lib/format";
import { useToast } from "../components/Toast";

const TABS = ["Overview", "Extracted Information", "Validation", "Review Items", "Source Content", "Ask Questions", "Audit History"];

function locationLabel(loc: any): string {
  if (!loc) return "—";
  if (loc.page) return `Page ${loc.page}`;
  if (loc.section) return `${loc.section}${loc.paragraph ? ` · Para ${loc.paragraph}` : ""}`;
  if (loc.sheet) return `Sheet ${loc.sheet}${loc.row ? `, Row ${loc.row}` : ""}${loc.column ? `, Col ${loc.column}` : ""}`;
  if (loc.line) return `Line ${loc.line}`;
  if (loc.json_path) return loc.json_path;
  if (loc.region) return "Image region";
  return "—";
}

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const [doc, setDoc] = useState<any>(null);
  const [tab, setTab] = useState("Overview");
  const [extractions, setExtractions] = useState<any>(null);
  const [validation, setValidation] = useState<any[] | null>(null);
  const [reviewItems, setReviewItems] = useState<any[] | null>(null);
  const [content, setContent] = useState<any[] | null>(null);
  const [audit, setAudit] = useState<any[] | null>(null);
  const [anomalies, setAnomalies] = useState<any[] | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<any>(null);
  const [asking, setAsking] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const toast = useToast();

  const load = () => id && api.getDocument(id).then(setDoc);

  useEffect(() => {
    load();
    const interval = setInterval(() => {
      if (doc?.status !== "ready" && doc?.status !== "failed") load();
    }, 3000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, doc?.status]);

  useEffect(() => {
    if (!id || !doc || doc.status !== "ready") return;
    if (tab === "Extracted Information" && !extractions) api.getExtractions(id).then(setExtractions);
    if (tab === "Validation" && !validation) api.getValidation(id).then(setValidation);
    if (tab === "Review Items" && !reviewItems) api.listReviewQueue("all").then((all) => setReviewItems(all.filter((r: any) => r.document_id === id)));
    if (tab === "Source Content" && !content) api.getDocumentContent(id).then(setContent);
    if (tab === "Audit History" && !audit) api.getAudit(id).then(setAudit);
    if (tab === "Overview" && !anomalies) api.getAnomalies(id).then(setAnomalies).catch(() => setAnomalies([]));
  }, [tab, id, doc, extractions, validation, reviewItems, content, audit, anomalies]);

  const handleDelete = async () => {
    if (!id || !confirm("Delete this document permanently? This cannot be undone.")) return;
    await api.deleteDocument(id);
    toast.show("Document deleted.", "success");
    window.location.href = "/documents";
  };

  const askQuestion = async (q: string) => {
    if (!id || !q.trim()) return;
    setAsking(true);
    setAnswer(null);
    try {
      const result = await api.query(q, [id]);
      setAnswer(result);
    } catch (e: any) {
      toast.show(e.message, "error");
    } finally {
      setAsking(false);
    }
  };

  if (!doc) {
    return (
      <div className="p-8 max-w-4xl space-y-4">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 max-w-5xl">
      <Link to="/documents" className="inline-flex items-center gap-1.5 text-sm text-inkmuted hover:text-ink mb-4">
        <ArrowLeft size={15} /> All documents
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-semibold text-ink break-all">{doc.filename}</h1>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <StatusPill status={doc.status} />
            <span className="text-xs text-inkmuted">{doc.file_type?.toUpperCase()} • {formatBytes(doc.size_bytes)} • Uploaded {formatDate(doc.created_at)}</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {doc.status === "ready" && (
            <div className="relative">
              <button
                onClick={() => setExportOpen((v) => !v)}
                className="flex items-center gap-1.5 text-sm border border-line bg-surface px-3.5 py-2 rounded-lg hover:border-brand-deep/60"
              >
                <Download size={15} /> Export
              </button>
              {exportOpen && (
                <div className="absolute right-0 mt-1 bg-surface border border-line rounded-lg shadow-soft overflow-hidden z-10 w-40">
                  {(["xlsx", "csv", "json"] as const).map((fmt) => (
                    <button
                      key={fmt}
                      onClick={async () => {
                        setExportOpen(false);
                        try {
                          await api.exportDocument(doc.id, fmt, doc.filename);
                        } catch (e: any) {
                          toast.show(e.message || "Export failed.", "error");
                        }
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-ink hover:bg-canvas"
                    >
                      {fmt === "xlsx" ? "Excel (.xlsx)" : fmt === "csv" ? "CSV (.csv)" : "JSON (.json)"}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          <button onClick={handleDelete} className="flex items-center gap-1.5 text-sm text-danger-deep border border-danger-deep/30 bg-danger-pastel px-3.5 py-2 rounded-lg">
            <Trash2 size={15} /> Delete
          </button>
        </div>
      </div>

      {doc.duplicate_of && (
        <div className="bg-peach-pastel text-peach-deep rounded-xl2 p-4 mb-4 flex items-start gap-2 text-sm">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          Possible duplicate detected ({Math.round((doc.duplicate_score || 0) * 100)}% similar to another document).
        </div>
      )}

      {doc.status !== "ready" && doc.status !== "failed" && (
        <div className="bg-surface border border-line rounded-xl2 p-6 mb-6">
          <p className="text-sm text-ink font-medium mb-2">{doc.status_message || "Processing..."}</p>
          <PipelineProgress status={doc.status} />
        </div>
      )}

      {doc.status === "failed" && (
        <div className="bg-danger-pastel text-danger-deep rounded-xl2 p-4 mb-6 text-sm">
          Processing failed: {doc.status_message}
        </div>
      )}

      {doc.status === "ready" && (
        <>
          <div className="flex gap-1 overflow-x-auto border-b border-line mb-6">
            {TABS.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`whitespace-nowrap px-3.5 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  tab === t ? "border-brand-deep text-brand-deep" : "border-transparent text-inkmuted hover:text-ink"
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          {tab === "Overview" && (
            <div className="grid md:grid-cols-3 gap-5">
              <div className="md:col-span-2 space-y-5">
                <div className="bg-surface border border-line rounded-xl2 p-5">
                  <h3 className="font-semibold text-ink mb-2">Executive summary</h3>
                  <p className="text-sm text-inkmuted leading-relaxed">{doc.summary?.executive_summary || "No summary available."}</p>
                  {doc.summary?.key_points?.length > 0 && (
                    <ul className="mt-3 space-y-1.5 list-disc pl-5">
                      {doc.summary.key_points.map((k: string, i: number) => <li key={i} className="text-sm text-inkmuted">{k}</li>)}
                    </ul>
                  )}
                </div>

                {doc.suggested_questions?.length > 0 && (
                  <div className="bg-surface border border-line rounded-xl2 p-5">
                    <h3 className="font-semibold text-ink mb-3 flex items-center gap-1.5"><Sparkles size={16} className="text-lavender-deep" /> Suggested questions</h3>
                    <div className="flex flex-wrap gap-2">
                      {doc.suggested_questions.map((q: string, i: number) => (
                        <button key={i} onClick={() => { setTab("Ask Questions"); setQuestion(q); askQuestion(q); }}
                          className="text-sm bg-lavender-pastel text-lavender-deep px-3 py-1.5 rounded-full hover:opacity-80">
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {anomalies && anomalies.length > 0 && (
                  <div className="bg-peach-pastel rounded-xl2 p-5">
                    <h3 className="font-semibold text-peach-deep mb-2 flex items-center gap-1.5"><AlertTriangle size={16} /> Anomalies detected</h3>
                    <ul className="space-y-1.5">
                      {anomalies.map((a, i) => <li key={i} className="text-sm text-peach-deep">{a.message}</li>)}
                    </ul>
                  </div>
                )}
              </div>

              <div className="bg-surface border border-line rounded-xl2 p-5 h-fit">
                <h3 className="font-semibold text-ink mb-3">Document quality</h3>
                <p className="text-3xl font-semibold font-mono text-ink">{doc.quality_score ?? "—"}<span className="text-base text-inkmuted">/100</span></p>
                <div className="mt-4 space-y-2">
                  {doc.quality_checks && Object.entries(doc.quality_checks).map(([k, v]: any) => (
                    <div key={k} className="flex items-center gap-2 text-sm">
                      {v ? <CheckCircle2 size={14} className="text-mint-deep" /> : <AlertTriangle size={14} className="text-peach-deep" />}
                      <span className="text-inkmuted capitalize">{k.replaceAll("_", " ")}</span>
                    </div>
                  ))}
                </div>
                {doc.pii_findings?.length > 0 && (
                  <p className="text-xs text-inkmuted mt-4 pt-4 border-t border-line">
                    Sensitive information detected: {doc.pii_findings.length} item(s)
                  </p>
                )}
              </div>
            </div>
          )}

          {tab === "Extracted Information" && (
            <div className="bg-surface border border-line rounded-xl2 overflow-hidden">
              {!extractions ? <Skeleton className="h-40 m-5" /> : extractions.verified_values.length === 0 ? (
                <EmptyState title="No verified fields yet." description="Fields are still awaiting review, or none were extracted." />
              ) : (
                <table className="w-full text-sm">
                  <thead className="bg-canvas text-inkmuted text-xs uppercase">
                    <tr><th className="text-left px-5 py-3 font-medium">Field</th><th className="text-left px-5 py-3 font-medium">Verified Value</th><th className="text-left px-5 py-3 font-medium">Corrected?</th></tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {extractions.verified_values.map((v: any) => (
                      <tr key={v.id}>
                        <td className="px-5 py-3 font-medium text-ink">{v.field_name}</td>
                        <td className="px-5 py-3 text-ink">{v.verified_value ?? <span className="text-inkmuted">Rejected</span>}</td>
                        <td className="px-5 py-3 text-inkmuted">{v.was_corrected ? "Yes" : "No"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {tab === "Validation" && (
            <div className="space-y-4">
              {!validation ? <Skeleton className="h-24 w-full" /> : (
                <>
                  <div className="flex flex-wrap gap-3">
                    {(() => {
                      const passed = validation.filter((v: any) => v.passed === "pass").length;
                      const warnings = validation.filter((v: any) => v.passed === "warning").length;
                      const failed = validation.filter((v: any) => v.passed === "fail").length;
                      return (
                        <>
                          <div className="flex items-center gap-2 bg-mint-pastel text-mint-deep rounded-full px-3.5 py-1.5 text-sm font-medium">
                            <CheckCircle2 size={14} /> {passed} passed
                          </div>
                          <div className="flex items-center gap-2 bg-peach-pastel text-peach-deep rounded-full px-3.5 py-1.5 text-sm font-medium">
                            <AlertTriangle size={14} /> {warnings} warning{warnings === 1 ? "" : "s"}
                          </div>
                          <div className="flex items-center gap-2 bg-danger-pastel text-danger-deep rounded-full px-3.5 py-1.5 text-sm font-medium">
                            <AlertTriangle size={14} /> {failed} failed
                          </div>
                        </>
                      );
                    })()}
                  </div>
                  <div className="space-y-3">
                    {validation.map((v: any) => (
                      <div key={v.id} className={`rounded-xl2 p-4 border ${v.passed === "fail" ? "bg-danger-pastel border-danger-deep/20" : v.passed === "warning" ? "bg-peach-pastel border-peach-deep/20" : "bg-mint-pastel border-mint-deep/20"}`}>
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium capitalize">{v.rule_name.replaceAll("_", " ")}</p>
                          <span className="text-xs uppercase tracking-wide opacity-70">{v.passed}</span>
                        </div>
                        <p className="text-sm mt-1.5 opacity-90 leading-relaxed">{v.message}</p>
                        {v.fields_involved?.length > 0 && (
                          <p className="text-xs mt-2 opacity-70">Fields: {v.fields_involved.join(", ")}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {tab === "Review Items" && (
            <div className="space-y-3">
              {!reviewItems ? <Skeleton className="h-24 w-full" /> : reviewItems.length === 0 ? (
                <EmptyState title="Everything is verified." description="You're all caught up." />
              ) : reviewItems.map((r: any) => (
                <div key={r.id} className="bg-surface border border-line rounded-xl2 p-4 flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-ink truncate">{r.field_name}</p>
                    <p className="text-sm text-inkmuted mt-0.5 line-clamp-2 break-words">{r.ai_value}</p>
                    <p className="text-xs text-inkmuted mt-1.5 capitalize">{r.status} • {locationLabel(r.source_location)}</p>
                  </div>
                  <ConfidenceBadge value={r.confidence} />
                </div>
              ))}
              <Link to="/review-queue" className="text-sm text-brand-deep font-medium">Go to full review queue →</Link>
            </div>
          )}

          {tab === "Source Content" && (
            <div className="space-y-3">
              {!content ? <Skeleton className="h-40 w-full" /> : content.map((c: any) => (
                <div key={c.id} className="bg-surface border border-line rounded-xl2 p-4">
                  <p className="text-xs text-inkmuted font-mono mb-1.5">{locationLabel(c.location)}</p>
                  {c.content_type === "table" && c.table_data ? (
                    <div className="overflow-x-auto">
                      <table className="text-sm w-full">
                        <thead><tr>{c.table_data.headers.map((h: string, i: number) => <th key={i} className="text-left pr-4 pb-1 text-inkmuted font-medium">{h}</th>)}</tr></thead>
                        <tbody>{c.table_data.rows.slice(0, 8).map((row: string[], ri: number) => (
                          <tr key={ri}>{row.map((cell, ci) => <td key={ci} className="pr-4 py-0.5 text-ink">{cell}</td>)}</tr>
                        ))}</tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-sm text-ink whitespace-pre-wrap">{c.text}</p>
                  )}
                </div>
              ))}
            </div>
          )}

          {tab === "Ask Questions" && (
            <div className="max-w-2xl">
              <div className="flex gap-2">
                <input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && askQuestion(question)}
                  placeholder="Ask a question about this document..."
                  className="flex-1 border border-line rounded-lg px-3.5 py-2.5 bg-surface text-sm focus:border-brand-deep outline-none"
                />
                <button onClick={() => askQuestion(question)} disabled={asking} className="bg-brand-deep text-white text-sm font-medium px-4 py-2.5 rounded-lg disabled:opacity-60">
                  {asking ? "Asking..." : "Ask"}
                </button>
              </div>

              {answer && (
                <div className="mt-5 bg-surface border border-line rounded-xl2 p-5 space-y-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-inkmuted">Answer</p>
                    <p className="font-medium text-ink mt-1">{answer.answer}</p>
                  </div>
                  {answer.grounded && (
                    <>
                      <div>
                        <p className="text-xs uppercase tracking-wide text-inkmuted">Confidence</p>
                        <ConfidenceBadge value={answer.confidence} />
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-wide text-inkmuted mb-2">Sources & evidence</p>
                        <div className="space-y-2">
                          {answer.sources.map((s: any, i: number) => (
                            <div key={i} className="bg-canvas rounded-lg p-3">
                              <p className="text-xs font-medium text-ink">{s.label}</p>
                              <p className="text-xs text-inkmuted mt-1">{s.evidence}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {tab === "Audit History" && (
            <div className="space-y-2">
              {!audit ? <Skeleton className="h-24 w-full" /> : audit.map((a: any) => (
                <div key={a.id} className="flex items-start gap-3 bg-surface border border-line rounded-xl2 p-4">
                  <div className="h-2 w-2 rounded-full bg-brand-deep mt-2 shrink-0" />
                  <div>
                    <p className="text-sm text-ink"><span className="font-medium capitalize">{a.action}</span>{a.field_name ? ` · ${a.field_name}` : ""}</p>
                    {(a.before_value || a.after_value) && (
                      <p className="text-xs text-inkmuted mt-0.5">{a.before_value ?? "—"} → {a.after_value ?? "—"}</p>
                    )}
                    <p className="text-xs text-inkmuted mt-0.5">{formatDate(a.created_at)} • {a.actor}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

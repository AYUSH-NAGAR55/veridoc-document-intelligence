import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { FileStack, Loader2, CheckCircle2, AlertTriangle, Database, ArrowRight } from "lucide-react";
import { api } from "../lib/api";
import FileTypeIcon from "../components/FileTypeIcon";
import StatusBadge from "../components/StatusBadge";

function StatCard({ icon: Icon, label, value, accent, delay }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      whileHover={{ y: -2 }}
      className="rounded-xl2 border border-border bg-surface p-5 shadow-soft"
    >
      <div className="flex items-center justify-between mb-3">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${accent}`}>
          <Icon size={16} />
        </div>
      </div>
      <p className="font-display text-2xl text-ink">{value}</p>
      <p className="text-xs text-ink-soft mt-0.5">{label}</p>
    </motion.div>
  );
}

// A restrained, tasteful nod to "floating document layers" -- three
// offset cards with depth via shadow and slight rotation, not a full 3D
// scene. Purely decorative, sits behind the page header.
function DocumentStack() {
  return (
    <div className="relative w-16 h-16 shrink-0" style={{ perspective: 600 }}>
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, rotate: 0, y: 0 }}
          animate={{ opacity: 1, rotate: (i - 1) * 6, y: -i * 3, x: i * 2 }}
          transition={{ delay: i * 0.1, type: "spring", stiffness: 200 }}
          className="absolute inset-0 rounded-lg border border-border shadow-soft"
          style={{
            background: i === 2 ? "#FFFFFF" : i === 1 ? "#FDFBF7" : "#FAF8F4",
            zIndex: 3 - i,
          }}
        />
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.getDashboard().then(setStats);
    const t = setInterval(() => api.getDashboard().then(setStats), 4000);
    return () => clearInterval(t);
  }, []);

  if (!stats) {
    return <div className="max-w-6xl mx-auto px-8 py-10 text-ink-soft">Loading…</div>;
  }

  return (
    <div className="max-w-6xl mx-auto px-8 py-10">
      <div className="flex items-center gap-4 mb-8">
        <DocumentStack />
        <div>
          <h1 className="font-display text-3xl text-ink">Dashboard</h1>
          <p className="text-ink-soft mt-1">Verification and knowledge overview across every document.</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard icon={FileStack} label="Total documents" value={stats.total_documents} accent="bg-primary-soft text-primary-deep" delay={0} />
        <StatCard icon={Loader2} label="Processing" value={stats.processing_documents} accent="bg-[#E9E5DC] text-ink-soft" delay={0.05} />
        <StatCard icon={CheckCircle2} label="Verified & ready" value={stats.ready_documents} accent="bg-sage-soft text-[#3F6350]" delay={0.1} />
        <StatCard icon={AlertTriangle} label="Needs review" value={stats.needs_review_documents} accent="bg-amber-soft text-[#7A5326]" delay={0.15} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="rounded-xl2 border border-border bg-surface p-5">
          <p className="text-xs text-ink-soft mb-1">Extracted fields</p>
          <p className="font-display text-xl text-ink">{stats.total_fields}</p>
        </motion.div>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.25 }} className="rounded-xl2 border border-border bg-surface p-5">
          <p className="text-xs text-ink-soft mb-1">Verified fields</p>
          <p className="font-display text-xl text-sage">{stats.verified_fields}</p>
        </motion.div>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="rounded-xl2 border border-border bg-surface p-5">
          <div className="flex items-center gap-2 mb-1">
            <Database size={13} className="text-ink-soft" />
            <p className="text-xs text-ink-soft">Vectors indexed for search</p>
          </div>
          <p className="font-display text-xl text-ink">{stats.indexed_vectors}</p>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-medium text-ink">Recent documents</h2>
            <Link to="/documents" className="text-xs text-primary-deep flex items-center gap-1 hover:underline">
              View all <ArrowRight size={12} />
            </Link>
          </div>
          <div className="space-y-2">
            {stats.recent_documents.length === 0 && (
              <p className="text-sm text-ink-soft py-6 text-center border border-dashed border-border rounded-xl2">No documents uploaded yet.</p>
            )}
            {stats.recent_documents.map((doc) => (
              <Link
                key={doc.id}
                to={`/documents/${doc.id}`}
                className="flex items-center gap-3 rounded-xl2 border border-border bg-surface px-4 py-3 hover:shadow-soft transition-shadow"
              >
                <FileTypeIcon fileType={doc.file_type} size={15} className="w-8 h-8" />
                <span className="flex-1 min-w-0 truncate text-sm text-ink">{doc.filename}</span>
                <StatusBadge status={doc.status} />
              </Link>
            ))}
          </div>
        </div>

        <div>
          <h2 className="font-medium text-ink mb-3">Recent review activity</h2>
          <div className="space-y-2">
            {stats.recent_reviews.length === 0 && (
              <p className="text-sm text-ink-soft py-6 text-center border border-dashed border-border rounded-xl2">No review decisions yet.</p>
            )}
            {stats.recent_reviews.map((r, i) => (
              <div key={i} className="rounded-xl2 border border-border bg-surface px-4 py-3 text-sm">
                <span className={`font-medium ${r.action === "reject" ? "text-[#8A4A3D]" : r.action === "correct" ? "text-amber" : "text-sage"}`}>
                  {r.action === "accept" ? "Accepted" : r.action === "reject" ? "Rejected" : "Corrected"}
                </span>
                {r.action === "correct" && (
                  <span className="text-ink-soft"> · {r.previous_value} → {r.new_value}</span>
                )}
                <p className="text-[11px] text-ink-soft mt-0.5">{new Date(r.created_at).toLocaleString()}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

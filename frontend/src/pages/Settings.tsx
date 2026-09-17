import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Skeleton } from "../components/shared";

export default function Settings() {
  const [health, setHealth] = useState<any>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setError(true));
  }, []);

  return (
    <div className="p-6 md:p-8 max-w-2xl">
      <h1 className="text-2xl font-semibold text-ink mb-6">Settings</h1>

      <div className="bg-surface border border-line rounded-xl2 p-5">
        <h2 className="font-semibold text-ink mb-4">Backend configuration</h2>
        {error ? (
          <p className="text-sm text-danger-deep">Could not reach the VeriDoc backend. Make sure it's running.</p>
        ) : !health ? (
          <Skeleton className="h-16 w-full" />
        ) : (
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between"><dt className="text-inkmuted">Status</dt><dd className="font-medium text-mint-deep">{health.status}</dd></div>
            <div className="flex justify-between"><dt className="text-inkmuted">LLM provider</dt><dd className="font-mono">{health.llm_provider}</dd></div>
            <div className="flex justify-between"><dt className="text-inkmuted">Database</dt><dd className="font-mono">{health.database}</dd></div>
          </dl>
        )}
        <p className="text-xs text-inkmuted mt-5 pt-4 border-t border-line">
          Provider, database, and OCR settings are configured via environment variables in the backend's
          <code className="mx-1 bg-canvas px-1.5 py-0.5 rounded">.env</code> file — see the README for details.
        </p>
      </div>
    </div>
  );
}

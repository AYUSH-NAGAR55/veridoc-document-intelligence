import { motion } from "framer-motion";
import clsx from "clsx";

const STEPS = ["Uploading", "Understanding", "Extracting", "Validating", "Verifying", "Indexing", "Ready"];

export function PipelineProgress({ status }: { status: string }) {
  const currentIndex = Math.max(
    0,
    STEPS.findIndex((s) => s.toLowerCase() === status?.toLowerCase())
  );
  const failed = status === "failed";

  return (
    <div className="w-full overflow-x-auto py-2">
      <div className="flex items-center min-w-max">
        {STEPS.map((step, i) => {
          const done = i < currentIndex || (i === currentIndex && status === "ready");
          const active = i === currentIndex && status !== "ready";
          return (
            <div key={step} className="flex items-center">
              <div className="flex flex-col items-center gap-1.5 w-20">
                <div
                  className={clsx(
                    "h-7 w-7 rounded-full flex items-center justify-center text-[11px] font-medium border",
                    failed && i === currentIndex
                      ? "bg-danger-pastel border-danger-deep text-danger-deep"
                      : done
                      ? "bg-mint-deep border-mint-deep text-white"
                      : active
                      ? "bg-brand-deep border-brand-deep text-white"
                      : "bg-surface border-line text-inkmuted"
                  )}
                >
                  {done ? "✓" : i + 1}
                </div>
                <span className={clsx("text-[11px] text-center", active ? "text-ink font-medium" : "text-inkmuted")}>
                  {step}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className="h-[2px] w-10 bg-line relative overflow-hidden -mt-4">
                  {i < currentIndex && (
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: "100%" }}
                      transition={{ duration: 0.4 }}
                      className="h-full bg-mint-deep absolute left-0 top-0"
                    />
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

"use client";

import type { ContextMessage } from "@/lib/types";

export default function ContextMeter({ context }: { context: ContextMessage | null }) {
  if (!context) {
    return (
      <div className="glass rounded-2xl p-5">
        <SectionTitle>Context engine</SectionTitle>
        <p className="text-sm text-muted mt-2">
          Run a request to see which files get selected, and how much of the repo
          gets left out on purpose.
        </p>
      </div>
    );
  }

  const maxScore = Math.max(...context.files.map((f) => f.score), 1);
  const sorted = [...context.files].sort((a, b) => b.score - a.score);

  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-baseline justify-between">
        <SectionTitle>Context engine</SectionTitle>
        <span className="font-display text-2xl text-coder">
          {context.compression_pct}%
          <span className="text-xs text-muted font-body ml-1.5">saved</span>
        </span>
      </div>
      <p className="text-xs text-muted mt-1">
        {context.included_tokens.toLocaleString()} of{" "}
        {context.full_repo_tokens.toLocaleString()} est. tokens sent to the
        agents · budget {context.budget.toLocaleString()}
      </p>

      <div className="mt-4 space-y-2">
        {sorted.map((f) => (
          <div key={f.path} className="group">
            <div className="flex items-center justify-between text-xs mb-1">
              <span
                className={`font-mono truncate ${
                  f.included ? "text-ink" : "text-faint line-through decoration-faint/60"
                }`}
              >
                {f.path}
              </span>
              <span className="text-faint shrink-0 ml-2">{f.tokens}t</span>
            </div>
            <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
              <div
                className={`h-full rounded-full ${f.included ? "bg-coder" : "bg-faint/40"}`}
                style={{ width: `${Math.max(4, (f.score / maxScore) * 100)}%` }}
              />
            </div>
            {f.included && f.matched_terms.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {f.matched_terms.slice(0, 5).map((t) => (
                  <span
                    key={t}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-coder/10 text-coder/80 font-mono"
                  >
                    {t}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-xs uppercase tracking-wider text-muted font-medium">
      {children}
    </h2>
  );
}

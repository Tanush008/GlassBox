"use client";

import { useEffect, useState } from "react";
import type { ContextMessage, RepoFile } from "@/lib/types";
import { SectionTitle } from "./ContextMeter";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RepoExplorer({ context }: { context: ContextMessage | null }) {
  const [files, setFiles] = useState<RepoFile[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/repo`)
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}`);
        return r.json();
      })
      .then((data) => {
        setFiles(data.files);
        setSelected(data.files[0]?.path ?? null);
      })
      .catch(() => setLoadError(`Couldn't reach ${API_URL}. Is the backend running?`));
  }, []);

  const statusFor = (path: string) => {
    if (!context) return null;
    const f = context.files.find((c) => c.path === path);
    return f ? f.included : null;
  };

  const activeContent = files.find((f) => f.path === selected)?.content ?? "";

  return (
    <div className="glass rounded-2xl p-5 flex flex-col h-full">
      <SectionTitle>TaskFlow API — sample repo</SectionTitle>
      {loadError && <p className="text-xs text-changes mt-2">{loadError}</p>}
      <div className="mt-3 flex flex-col sm:flex-row gap-3 flex-1 min-h-0">
        <ul className="sm:w-48 shrink-0 space-y-0.5 overflow-y-auto max-h-56 sm:max-h-none">
          {files.map((f) => {
            const included = statusFor(f.path);
            return (
              <li key={f.path}>
                <button
                  onClick={() => setSelected(f.path)}
                  className={`w-full text-left text-xs font-mono px-2 py-1.5 rounded-md truncate transition-colors ${
                    selected === f.path ? "bg-white/10 text-ink" : "text-muted hover:text-ink hover:bg-white/5"
                  }`}
                  title={f.path}
                >
                  <span
                    className={`inline-block h-1.5 w-1.5 rounded-full mr-1.5 ${
                      included === true ? "bg-coder" : included === false ? "bg-faint/40" : "bg-transparent"
                    }`}
                  />
                  {f.path}
                </button>
              </li>
            );
          })}
        </ul>
        <pre className="flex-1 text-[11px] font-mono leading-relaxed overflow-auto rounded-xl bg-black/40 border border-line p-3 min-h-[180px] max-h-80">
          {activeContent || " "}
        </pre>
      </div>
    </div>
  );
}

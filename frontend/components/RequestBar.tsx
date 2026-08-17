"use client";

import { useState } from "react";
import type { RunStatus } from "@/lib/types";

const SAMPLES = [
  "Add email validation when a user signs up",
  "Let tasks be filtered by completed status",
  "Reject empty task titles with a clear error",
];

export default function RequestBar({
  status,
  onRun,
}: {
  status: RunStatus;
  onRun: (request: string) => void;
}) {
  const [value, setValue] = useState("");
  const busy = status === "connecting" || status === "running";

  const submit = () => {
    if (!value.trim() || busy) return;
    onRun(value.trim());
  };

  return (
    <div className="glass rounded-2xl p-4 sm:p-5">
      <label htmlFor="request" className="block text-xs uppercase tracking-wider text-muted mb-2">
        Describe a change to TaskFlow API
      </label>
      <div className="flex flex-col sm:flex-row gap-3">
        <textarea
          id="request"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
          }}
          rows={2}
          placeholder="e.g. Add email validation when a user signs up"
          className="flex-1 resize-none rounded-xl bg-black/30 border border-line px-4 py-3 text-sm sm:text-base placeholder:text-faint focus:border-coder/60 outline-none transition-colors"
        />
        <button
          onClick={submit}
          disabled={busy || !value.trim()}
          className="shrink-0 rounded-xl px-5 py-3 font-medium text-sm bg-coder text-deep disabled:bg-white/10 disabled:text-faint transition-colors hover:bg-coder/90 self-start sm:self-stretch"
        >
          {busy ? "Running…" : "Run agents"}
        </button>
      </div>
      <div className="flex flex-wrap gap-2 mt-3">
        {SAMPLES.map((s) => (
          <button
            key={s}
            onClick={() => setValue(s)}
            disabled={busy}
            className="text-xs px-3 py-1.5 rounded-full border border-line text-muted hover:text-ink hover:border-white/20 transition-colors disabled:opacity-40"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

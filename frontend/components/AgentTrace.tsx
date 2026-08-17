"use client";

import type { AgentName, AgentResultMessage, RunStatus } from "@/lib/types";
import DiffView from "./DiffView";
import { SectionTitle } from "./ContextMeter";

const AGENT_STYLES: Record<AgentName, { border: string; text: string; bg: string; dot: string }> = {
  Planner: { border: "border-l-planner", text: "text-planner", bg: "bg-planner/10", dot: "bg-planner" },
  Coder: { border: "border-l-coder", text: "text-coder", bg: "bg-coder/10", dot: "bg-coder" },
  Reviewer: { border: "border-l-reviewer", text: "text-reviewer", bg: "bg-reviewer/10", dot: "bg-reviewer" },
};

function ReviewerContent({ content }: { content: string }) {
  const [firstLine, ...rest] = content.split("\n");
  const approved = firstLine.toUpperCase().includes("APPROVE") && !firstLine.toUpperCase().includes("REQUEST");
  return (
    <div>
      <span
        className={`inline-block text-[11px] font-medium px-2 py-0.5 rounded-full mb-2 ${
          approved ? "bg-approve/15 text-approve" : "bg-changes/15 text-changes"
        }`}
      >
        {approved ? "Approved" : "Changes requested"}
      </span>
      <p className="text-sm text-ink/90 leading-relaxed">{rest.join("\n").trim()}</p>
    </div>
  );
}

function TraceCard({ msg }: { msg: AgentResultMessage }) {
  const style = AGENT_STYLES[msg.agent];
  return (
    <div className={`glass rounded-xl border-l-4 ${style.border} p-4 animate-rise`}>
      <div className="flex items-center gap-2 mb-2">
        <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
        <span className={`text-xs font-medium ${style.text}`}>{msg.agent}</span>
        <span className="text-[11px] text-faint">round {msg.round}</span>
      </div>
      {msg.agent === "Coder" ? (
        <DiffView diff={msg.content} />
      ) : msg.agent === "Reviewer" ? (
        <ReviewerContent content={msg.content} />
      ) : (
        <p className="text-sm text-ink/90 leading-relaxed whitespace-pre-wrap">{msg.content}</p>
      )}
    </div>
  );
}

export default function AgentTrace({
  trace,
  status,
}: {
  trace: AgentResultMessage[];
  status: RunStatus;
}) {
  return (
    <div className="glass rounded-2xl p-5 flex flex-col min-h-[320px]">
      <div className="flex items-center justify-between">
        <SectionTitle>Agent trace</SectionTitle>
        {(status === "connecting" || status === "running") && (
          <span className="flex items-center gap-1.5 text-[11px] text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-coder animate-pulse" />
            live
          </span>
        )}
      </div>

      <div className="mt-3 space-y-3 flex-1">
        {trace.length === 0 && status === "idle" && (
          <p className="text-sm text-muted">
            The Planner, Coder, and Reviewer will show up here, in order, as they run.
            Nothing is hidden between them.
          </p>
        )}
        {trace.length === 0 && (status === "connecting" || status === "running") && (
          <p className="text-sm text-muted animate-pulse">Selecting context…</p>
        )}
        {trace.map((msg, i) => (
          <TraceCard key={i} msg={msg} />
        ))}
      </div>
    </div>
  );
}

"use client";

import RequestBar from "@/components/RequestBar";
import RepoExplorer from "@/components/RepoExplorer";
import ContextMeter from "@/components/ContextMeter";
import AgentTrace from "@/components/AgentTrace";
import { useAgentSocket } from "@/lib/useAgentSocket";

export default function Home() {
  const { status, context, trace, result, error, run } = useAgentSocket();

  return (
    <main className="max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
      <header className="mb-8">
        <div className="flex items-center gap-2 mb-3">
          <span className="h-2.5 w-2.5 rounded-sm bg-coder" />
          <span className="text-xs uppercase tracking-[0.2em] text-muted">Glassbox</span>
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-bold leading-tight max-w-2xl">
          An AI agent harness with{" "}
          <span className="text-coder">nothing hidden</span>.
        </h1>
        <p className="text-muted mt-3 max-w-2xl text-sm sm:text-base">
          Type a change you want made to a small demo API. Watch the context engine
          decide which files matter, then watch a Planner, a Coder, and a Reviewer
          argue it out — every step visible, none of it summarized away.
        </p>
      </header>

      <div className="mb-6">
        <RequestBar status={status} onRun={run} />
        {error && (
          <p className="text-sm text-changes mt-3 glass rounded-xl px-4 py-3">{error}</p>
        )}
        {result && (
          <div className="glass rounded-xl px-4 py-3 mt-3 flex items-center gap-3 text-sm animate-rise">
            <span
              className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                result.approved ? "bg-approve/15 text-approve" : "bg-changes/15 text-changes"
              }`}
            >
              {result.approved ? "Approved" : "Shipped after max rounds"}
            </span>
            <span className="text-muted">
              {result.rounds} review round{result.rounds === 1 ? "" : "s"}
            </span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)] gap-5">
        <div className="flex flex-col gap-5">
          <RepoExplorer context={context} />
          <ContextMeter context={context} />
        </div>
        <AgentTrace trace={trace} status={status} />
      </div>

      <footer className="mt-14 text-xs text-faint text-center">
        Built for the Superbrain AI Engineer assignment — context selection and
        agent orchestration run for real against the Anthropic API, on a small
        in-repo demo codebase.
      </footer>
    </main>
  );
}

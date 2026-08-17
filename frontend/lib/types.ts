export type RepoFile = {
  path: string;
  content: string;
};

export type ContextFile = {
  path: string;
  score: number;
  tokens: number;
  included: boolean;
  matched_terms: string[];
};

export type ContextMessage = {
  type: "context";
  files: ContextFile[];
  included_tokens: number;
  full_repo_tokens: number;
  budget: number;
  compression_pct: number;
};

export type AgentName = "Planner" | "Coder" | "Reviewer";

export type AgentResultMessage = {
  type: "agent_result";
  agent: AgentName;
  round: number;
  content: string;
};

export type DoneMessage = {
  type: "done";
  final_diff: string;
  approved: boolean;
  rounds: number;
};

export type ErrorMessage = {
  type: "error";
  message: string;
};

export type ServerMessage =
  | ContextMessage
  | AgentResultMessage
  | DoneMessage
  | ErrorMessage;

export type RunStatus = "idle" | "connecting" | "running" | "done" | "error";

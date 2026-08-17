from typing import List, Optional

from pydantic import BaseModel


class RepoFile(BaseModel):
    path: str
    content: str


class RepoResponse(BaseModel):
    files: List[RepoFile]


class RunRequest(BaseModel):
    request: str


class ContextFileOut(BaseModel):
    path: str
    score: float
    tokens: int
    included: bool
    matched_terms: List[str]


class ContextMessage(BaseModel):
    type: str = "context"
    files: List[ContextFileOut]
    included_tokens: int
    full_repo_tokens: int
    budget: int
    compression_pct: float


class AgentResultMessage(BaseModel):
    type: str = "agent_result"
    agent: str
    round: int
    content: str


class DoneMessage(BaseModel):
    type: str = "done"
    final_diff: str
    approved: bool
    rounds: int


class ErrorMessage(BaseModel):
    type: str = "error"
    message: str

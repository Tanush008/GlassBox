"""
The Agent harness.

Three nodes, one loop:

    planner -> coder -> reviewer --(approved or out of rounds)--> END
                  ^                    |
                  '--(request changes)-'

Each node is a plain async function that makes one Anthropic API call - no
hidden magic, which is the point: this is meant to be a small, readable
stand-in for Superbrain's "Agent" component, not a production framework.
"""
from __future__ import annotations

from typing import Optional, TypedDict

from groq import AsyncGroq
from langgraph.graph import END, StateGraph

from .. import config
from . import prompts


class PipelineState(TypedDict, total=False):
    request: str
    context_text: str
    plan: str
    diff: str
    review_verdict: str
    review_feedback: str
    iteration: int
    max_iterations: int


_client: Optional[AsyncGroq] = None


def get_client() -> AsyncGroq:
    global _client
    if _client is None:
        if not config.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy backend/.env.example to "
                "backend/.env and add your key."
            )
        _client = AsyncGroq(api_key=config.GROQ_API_KEY)
    return _client


async def _call(system: str, user: str) -> str:
    client = get_client()
    resp = await client.chat.completions.create(
        model=config.MODEL_NAME,
        max_tokens=config.MAX_TOKENS_PER_CALL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return (resp.choices[0].message.content or "").strip()


async def planner_node(state: PipelineState) -> PipelineState:
    user = f"Request:\n{state['request']}\n\nContext files:\n{state['context_text']}"
    plan = await _call(prompts.PLANNER_SYSTEM, user)
    return {"plan": plan}


async def coder_node(state: PipelineState) -> PipelineState:
    feedback_block = ""
    if state.get("review_feedback"):
        feedback_block = (
            "\n\nReviewer feedback from the previous round "
            f"(address this directly):\n{state['review_feedback']}"
        )
    user = (
        f"Request:\n{state['request']}\n\n"
        f"Plan:\n{state['plan']}\n\n"
        f"Context files:\n{state['context_text']}"
        f"{feedback_block}"
    )
    diff = await _call(prompts.CODER_SYSTEM, user)
    return {"diff": diff}


async def reviewer_node(state: PipelineState) -> PipelineState:
    user = f"Request:\n{state['request']}\n\nDiff:\n{state['diff']}"
    raw = await _call(prompts.REVIEWER_SYSTEM, user)

    verdict = "REQUEST_CHANGES"
    feedback = raw
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("VERDICT:"):
            verdict = stripped.split(":", 1)[1].strip().upper()
        elif stripped.upper().startswith("FEEDBACK:"):
            feedback = stripped.split(":", 1)[1].strip()

    return {
        "review_verdict": verdict,
        "review_feedback": feedback,
        "iteration": state.get("iteration", 0) + 1,
    }


def _route_after_review(state: PipelineState) -> str:
    approved = state.get("review_verdict", "").upper().startswith("APPROVE")
    exhausted = state.get("iteration", 0) >= state.get("max_iterations", 2)
    if approved or exhausted:
        return END
    return "coder"


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("planner", planner_node)
    graph.add_node("coder", coder_node)
    graph.add_node("reviewer", reviewer_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "coder")
    graph.add_edge("coder", "reviewer")
    graph.add_conditional_edges(
        "reviewer", _route_after_review, {"coder": "coder", END: END}
    )

    return graph.compile()

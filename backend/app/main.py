from __future__ import annotations

import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .agents.graph import build_graph
from .context_engine import select_context
from .schemas import ContextFileOut, RepoFile, RepoResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("glassbox")

app = FastAPI(title="Glassbox API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_graph = build_graph()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/repo", response_model=RepoResponse)
async def get_repo():
    """Return every file in the sample repo so the frontend can render a
    file explorer, independent of whatever the context engine ends up
    selecting for a given request."""
    files = []
    for path in sorted(config.SAMPLE_REPO_DIR.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            files.append(
                RepoFile(
                    path=str(path.relative_to(config.SAMPLE_REPO_DIR)),
                    content=path.read_text(encoding="utf-8"),
                )
            )
    return RepoResponse(files=files)


AGENT_LABELS = {"planner": "Planner", "coder": "Coder", "reviewer": "Reviewer"}


def _format_context_block(included) -> str:
    parts = []
    for fs in included:
        parts.append(f"### {fs.path}\n```\n{fs.content}\n```")
    return "\n\n".join(parts)


@app.websocket("/ws/run")
async def run_pipeline(ws: WebSocket):
    await ws.accept()
    try:
        raw = await ws.receive_text()
        payload = json.loads(raw)
        user_request = (payload.get("request") or "").strip()
        if not user_request:
            await ws.send_json({"type": "error", "message": "Empty request."})
            await ws.close()
            return

        # --- 1. Context engine ---
        ctx = select_context(
            request=user_request,
            repo_path=config.SAMPLE_REPO_DIR,
            budget=config.CONTEXT_TOKEN_BUDGET,
        )

        context_files_out = [
            ContextFileOut(
                path=fs.path,
                score=fs.score,
                tokens=fs.tokens,
                included=True,
                matched_terms=fs.matched_terms,
            )
            for fs in ctx.included
        ] + [
            ContextFileOut(
                path=fs.path,
                score=fs.score,
                tokens=fs.tokens,
                included=False,
                matched_terms=fs.matched_terms,
            )
            for fs in ctx.excluded
        ]

        await ws.send_json(
            {
                "type": "context",
                "files": [f.model_dump() for f in context_files_out],
                "included_tokens": ctx.included_tokens,
                "full_repo_tokens": ctx.full_repo_tokens,
                "budget": ctx.budget,
                "compression_pct": ctx.compression_pct,
            }
        )

        # --- 2. Agent pipeline (streamed) ---
        initial_state = {
            "request": user_request,
            "context_text": _format_context_block(ctx.included),
            "iteration": 0,
            "max_iterations": config.MAX_REVIEW_ITERATIONS,
        }

        round_num = 1
        final_diff = ""
        approved = False

        async for update in _graph.astream(initial_state, stream_mode="updates"):
            for node_name, partial_state in update.items():
                if node_name == "planner":
                    await ws.send_json(
                        {
                            "type": "agent_result",
                            "agent": "Planner",
                            "round": round_num,
                            "content": partial_state.get("plan", ""),
                        }
                    )
                elif node_name == "coder":
                    final_diff = partial_state.get("diff", final_diff)
                    await ws.send_json(
                        {
                            "type": "agent_result",
                            "agent": "Coder",
                            "round": round_num,
                            "content": final_diff,
                        }
                    )
                elif node_name == "reviewer":
                    verdict = partial_state.get("review_verdict", "")
                    approved = verdict.upper().startswith("APPROVE")
                    await ws.send_json(
                        {
                            "type": "agent_result",
                            "agent": "Reviewer",
                            "round": round_num,
                            "content": (
                                f"VERDICT: {verdict}\n"
                                f"{partial_state.get('review_feedback', '')}"
                            ),
                        }
                    )
                    round_num += 1

        await ws.send_json(
            {
                "type": "done",
                "final_diff": final_diff,
                "approved": approved,
                "rounds": round_num - 1,
            }
        )

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except RuntimeError as e:
        # e.g. missing GROQ_API_KEY
        await ws.send_json({"type": "error", "message": str(e)})
    except Exception as e:  # noqa: BLE001
        logger.exception("Pipeline failed")
        await ws.send_json({"type": "error", "message": f"Pipeline error: {e}"})
    finally:
        try:
            await ws.close()
        except RuntimeError:
            pass

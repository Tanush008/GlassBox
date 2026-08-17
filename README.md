# Glassbox

An AI agent harness with nothing hidden. Type a change you want made to a
small demo API, and watch two things happen in the open that most agent
tools hide:

1. A **context engine** decides which files in the repo are actually
   relevant to your request, and tells you exactly why (matched terms,
   relevance score, token cost) and how much of the repo it left out.
2. A **Planner → Coder → Reviewer** agent loop plans the change, writes it
   as a diff, and critiques it - looping back to the Coder with concrete
   feedback if the Reviewer isn't satisfied - all streamed live, step by
   step, instead of arriving as one opaque final answer.

Built as the take-home assignment for the Founding AI Engineer role
(Superbrain / Open Gigantic).

---

## Why this project

Superbrain's own pitch has three parts: an IDE, an Agent harness, and a
context engine that compresses/prioritizes repo context and claims 60-80%
token savings. Rather than build something unrelated, I built a small,
fully transparent version of the same idea - a real (if much simpler)
context engine and a real multi-agent harness, both instrumented so every
decision is visible in the UI instead of collapsed into a spinner. The
name is the thesis: most agent products are a black box you feed a prompt
and wait; this one shows its work.

## Architecture

```
┌─────────────────────┐        WebSocket (/ws/run)        ┌──────────────────────┐
│   Next.js frontend   │ ───────────────────────────────▶ │   FastAPI backend     │
│   (Vercel)           │ ◀─────────────────────────────── │   (Render / Fly / …)  │
└─────────────────────┘     streamed JSON messages         └──────────────────────┘
                                                                      │
                                                    ┌─────────────────┼─────────────────┐
                                                    ▼                 ▼                 ▼
                                            context_engine.py   agents/graph.py    sample_repo/
                                            (relevance scoring,  (LangGraph:        (a small demo
                                             token budgeting)     Planner→Coder→     FastAPI app the
                                                                   Reviewer loop,    agents edit)
                                                                   Anthropic calls)
```

**Backend** - FastAPI + LangGraph + the Groq API.
- `context_engine.py`: walks the sample repo, scores every file's
  relevance to the request (keyword/identifier overlap, with a name-match
  boost), and greedily packs the highest-scoring files into a fixed token
  budget. Reports what got in, what got left out, and the resulting
  compression %. Deliberately dependency-free (no embedding model, no
  network call) so it's fast, free to run, and easy to reason about - see
  "What I'd change next" below for what a production version would add.
- `agents/graph.py`: a LangGraph `StateGraph` with three nodes -
  `planner`, `coder`, `reviewer` - each a plain async function making one
  Groq API call. The reviewer routes back to the coder with its
  feedback if it doesn't approve, up to `MAX_REVIEW_ITERATIONS` rounds,
  then the graph ends either way so the user always gets a diff.
- `main.py`: one REST endpoint (`GET /api/repo`, for the file explorer)
  and one WebSocket (`/ws/run`) that runs the context engine, streams a
  `context` message, then streams an `agent_result` message after every
  node the graph executes (via `graph.astream(..., stream_mode="updates")`),
  and finishes with a `done` message carrying the final diff.
- `sample_repo/`: a small, real, working FastAPI app ("TaskFlow API" -
  users, tasks, auth) that the agents actually read and edit. It has its
  own passing test suite (`pytest app/sample_repo/tests`), so it's a
  credible target for a code-change request, not a toy string.

**Frontend** - Next.js 14 (App Router) + TypeScript + Tailwind, no
component library, one WebSocket hook (`lib/useAgentSocket.ts`) owning
the whole run's state. Agents are color-coded (amber/teal/violet for
Planner/Coder/Reviewer) and that same color coding carries through the
context meter and file explorer, so the UI itself teaches you which
agent is "looking at" which file.

### Why the backend isn't also on Vercel

The assignment asks for the deployed app on Vercel, and the frontend is.
The backend needs a WebSocket connection held open for the whole
duration of a multi-round agent run (can be 10-30+ seconds), which
doesn't fit Vercel's serverless function model well. Rather than fake a
polling-based workaround that would undersell the "live trace" idea, I
deployed the backend on a host built for long-lived connections
(Render/Fly - see below) and pointed the Vercel frontend at it. I'd
rather ship the honest architecture and explain the trade-off than paper
over it.

## Decision log (the "why" behind the key choices)

- **Keyword-overlap context scoring instead of embeddings.** An
  embedding-based retriever would generalize better (e.g. matching
  "credentials" to "password" without a shared token), but it costs a
  network call and an API key per request, and it's a black box in its
  own right - harder to show *why* a file was picked. For a demo whose
  whole point is transparency, being able to point at the exact matched
  terms mattered more than retrieval quality. Noted as the first thing
  I'd swap in for a real repo (see Product Strategy, below).
- **Approximate token counts (`len(text) // 4`) instead of a real
  tokenizer.** I first wired up `tiktoken`, but it downloads its BPE
  file from a Microsoft-hosted blob on first use, which fails in
  network-locked environments (I hit this myself while building). A
  real tokenizer call is exact; a `chars/4` estimate is close enough to
  show *relative* compression and removes an external dependency and a
  point of failure entirely. This is a deliberate accuracy-for-
  robustness trade, not an oversight.
- **A hard cap on review rounds (`MAX_REVIEW_ITERATIONS`, default 2)
  instead of looping until approved.** An ungated loop is a real
  failure mode for agent products - a stubborn Reviewer and a Coder that
  can't satisfy it will spin forever and burn API spend. Capping it
  means the user always gets a result, and the UI is honest about
  whether it was actually approved or just timed out ("Shipped after
  max rounds").
- **LangGraph over a hand-rolled loop.** The state machine here is
  simple enough to write by hand, but I'd already reached for LangGraph
  on a previous multi-agent project (a PR-review bot) and it's the right
  tool once you want conditional routing, not because the graph is
  complex today but because it's the same shape the harness will need
  once there are more than three agents.
- **A small first-party sample repo instead of connecting to a real
  GitHub repo.** Reading a live repo (GitHub API + OAuth) is more
  impressive on paper, but it adds a whole auth flow that has nothing to
  do with what this assignment is actually testing (context selection +
  agent orchestration), and it makes the demo dependent on the state of
  someone's real repository. A small, purpose-built repo keeps every run
  reproducible and keeps the file list short enough that a reviewer can
  sanity-check the context engine's choices by eye.

## Running it locally

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your GROQ_API_KEY
uvicorn app.main:app --reload
```

Or with Docker:

```bash
cp backend/.env.example backend/.env   # then add your GROQ_API_KEY
docker compose up --build
```

Runs at `http://localhost:8000`. Sanity-check with:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/repo
python -m pytest backend/app/sample_repo/tests -q   # the demo repo's own tests
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # defaults already point at localhost:8000
npm run dev
```

Open `http://localhost:3000`, type a request (or click a sample prompt),
hit **Run agents**.

## Deploying

**Frontend → Vercel.** Import the `frontend/` directory as the project
root, set `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` (`wss://...`) to
your deployed backend, deploy.

**Backend → Render / Fly / Railway (anything that runs a long-lived
process).**
- Render: "New Web Service" → point at `backend/`, it'll pick up the
  `Dockerfile` → set `GROQ_API_KEY` and `ALLOWED_ORIGINS` (your
  Vercel URL) as environment variables.
- Fly: `fly launch` from `backend/`, `fly secrets set GROQ_API_KEY=...`.

Once both are up, update the frontend's env vars to the live backend URL
and redeploy.

## Environment variables

| File | Variable | What it does |
|---|---|---|
| `backend/.env` | `GROQ_API_KEY` | Required. No key, no agent calls. |
| `backend/.env` | `MODEL_NAME` | Defaults to `openai/gpt-oss-20b`. |
| `backend/.env` | `CONTEXT_TOKEN_BUDGET` | Lower it to see more aggressive compression. |
| `backend/.env` | `MAX_REVIEW_ITERATIONS` | Cap on Coder↔Reviewer rounds. |
| `backend/.env` | `ALLOWED_ORIGINS` | CORS - your frontend's origin. |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL` | Backend REST base URL. |
| `frontend/.env.local` | `NEXT_PUBLIC_WS_URL` | Backend WebSocket URL (`ws://` locally, `wss://` in prod). |

---

## Product Strategy

### A. If I were building Superbrain, what would I change or add next, and why?

**1. Make the context engine's decisions inspectable, the way Glassbox's
is.** The pitch is "60-80% token savings while keeping full repo
awareness" - the second half of that claim is the one users can't verify
today. If I were leading this product, the highest-leverage next feature
isn't a new capability, it's a trust feature: a panel (or even just a
hover tooltip in the IDE) showing which files got included in context
for the current agent turn and why. Right now the user has to take the
compression ratio on faith; showing the work turns "trust me" into
"check for yourself," which matters a lot the first time the agent
misses something because a relevant file got compressed out.

**2. Selective, reviewable context inclusion.** Related to the above -
today the engine decides for you. I'd add a lightweight way to pin a
file into context ("always include this") or exclude one, especially for
files that are relevant but keep losing the relevance-scoring lottery
(shared config, a style guide, a schema file). This is a small feature
with an outsized effect on trust, because it turns "the tool guessed
wrong" into "I told the tool what I know and it listened."

**3. A cheaper, faster "reviewer" pass before the expensive one.** Right
now (as far as the public description goes) it's the Agent that does the
work, full stop. Borrowing from Glassbox's own review loop: a fast, cheap
self-check pass (does this diff even parse, does it touch files outside
what was in context, does it match the stated plan) before the
expensive/slow full review, would catch a class of embarrassing failures
without burning a full review-model call every time.

### B. What major UI issues do I dislike, and how do they annoy current users?

*(Framed from the perspective of someone using AI coding IDEs generally,
since Superbrain wasn't hands-on-testable in the time I had - I'd revise
this section with specifics once inside the actual product.)*

- **Agent output arrives as one wall of text at the end, not as a
  trace.** The most common frustration with agent-in-IDE tools is not
  knowing whether the agent is stuck, thinking, or about to do something
  destructive, until it's already done it. Users end up re-reading a huge
  diff after the fact instead of steering mid-flight. This is the exact
  problem Glassbox's live trace panel is a small answer to.
- **No cheap way to say "not that file."** When an agent edits the wrong
  file because it guessed at repo structure, the recovery path is usually
  "revert everything and re-prompt with more detail" rather than a quick
  correction. That's expensive in both tokens and patience.
- **Diff review inside chat-style panels is cramped.** A unified diff in
  a narrow sidebar, without syntax highlighting or the ability to comment
  inline, makes reviewing a multi-file change meaningfully harder than
  reviewing the same change as a real PR - which is exactly the moment
  users most need clarity, since it's when they're deciding whether to
  accept AI-written code.

---

## What I'd do with more time

- Swap the keyword-overlap context scorer for a real embedding-based
  retriever (with the keyword version kept as a zero-cost fallback when
  no embedding API key is set).
- Persist runs (SQLite) so a request/trace/diff can be revisited later
  instead of living only in the browser tab.
- Let a user point the tool at their own small GitHub repo instead of
  only the bundled sample.
- Add automated CI (GitHub Actions) running the backend test suite and
  the frontend build on every push.

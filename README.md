# Glassbox

An AI agent harness with nothing hidden. Type a change you want made to a
small demo API, and watch two things happen live instead of behind a
spinner:

1. A **context engine** picks which files in the repo are relevant to
   your request, and shows why — matched terms, relevance score, token
   cost, and how much of the repo it left out.
2. A **Planner → Coder → Reviewer** agent loop plans the change, writes
   it as a diff, and reviews it — looping back to the Coder with
   feedback if the Reviewer isn't satisfied — streamed step by step.

Built for the Founding AI Engineer take-home (Superbrain / Open
Gigantic). Full write-up (what/why, decisions, product-strategy answers)
is in `ASSIGNMENT_ANSWERS.md` — this file is just "how to run it."

## Architecture

```
┌──────────────────┐   WebSocket (/ws/run)   ┌───────────────────┐
│ Next.js frontend  │ ──────────────────────▶ │ FastAPI backend   │
│ (Vercel)          │ ◀────────────────────── │ (Render / Fly)    │
└──────────────────┘   streamed JSON msgs     └───────────────────┘
                                                        │
                              ┌─────────────────────────┼─────────────────────┐
                              ▼                          ▼                     ▼
                      context_engine.py         agents/graph.py        sample_repo/
                      (relevance scoring,        (LangGraph:            (small demo
                       token budgeting)           Planner→Coder→          FastAPI app
                                                   Reviewer loop,          the agents
                                                   Groq API calls)         edit)
```

- **`context_engine.py`** — scores every file in the sample repo against
  the request (keyword/identifier overlap) and packs the top-scoring
  files into a fixed token budget. No embeddings, no network call —
  deliberately dependency-free so it's fast and easy to reason about.
- **`agents/graph.py`** — a LangGraph state machine: `planner` → `coder`
  → `reviewer`, with the reviewer routing back to the coder (up to
  `MAX_REVIEW_ITERATIONS` rounds) if it requests changes.
- **`main.py`** — one REST endpoint (`GET /api/repo`) and one WebSocket
  (`/ws/run`) that streams the context decision, then each agent step,
  then a final `done` message with the diff.
- **`sample_repo/`** — a small real FastAPI app ("TaskFlow API") the
  agents actually read and edit, with its own passing tests.
- **Frontend** — Next.js 14 + TypeScript + Tailwind, one WebSocket hook
  owning the run's state, agents color-coded (amber/teal/violet).

**Why the backend isn't also on Vercel:** a multi-round agent run holds
a WebSocket open for 10-30+ seconds, which doesn't fit Vercel's
serverless model. The frontend is on Vercel as required; the backend is
deployed somewhere built for long-lived connections instead of faking a
polling workaround.

## Running it locally

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY
uvicorn app.main:app --reload
```

Or with Docker: `cp backend/.env.example backend/.env` (add your key),
then `docker compose up --build`.

Check it's alive:
```bash
curl http://localhost:8000/api/health
python -m pytest backend/app/sample_repo/tests -q   # demo repo's own tests
```

**Frontend**

```bash
cd frontend
npm install
cp .env.local.example .env.local   # defaults already point at localhost:8000
npm run dev
```

Open `http://localhost:3000`, type a request (or click a sample prompt),
hit **Run agents**.

## Deploying

**Frontend → Vercel.** Import `frontend/` as the project root, set
`NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` (`wss://...`) to your
deployed backend, deploy.

**Backend → Render / Fly / Railway** (anything running a long-lived
process, not serverless).
- Render: "New Web Service" → point at `backend/` (picks up the
  `Dockerfile`) → set `GROQ_API_KEY` and `ALLOWED_ORIGINS`.
- Fly: `fly launch` from `backend/`, `fly secrets set GROQ_API_KEY=...`.

## Environment variables

| File | Variable | What it does |
|---|---|---|
| `backend/.env` | `GROQ_API_KEY` | Required. No key, no agent calls. |
| `backend/.env` | `MODEL_NAME` | Defaults to `openai/gpt-oss-120b`. Groq retires models with a few months' notice — a `model_not_found` 404 means check `console.groq.com/docs/models` and update this. |
| `backend/.env` | `CONTEXT_TOKEN_BUDGET` | Lower it to see more aggressive compression. |
| `backend/.env` | `MAX_REVIEW_ITERATIONS` | Cap on Coder↔Reviewer rounds. |
| `backend/.env` | `ALLOWED_ORIGINS` | CORS — your frontend's origin. |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL` | Backend REST base URL. |
| `frontend/.env.local` | `NEXT_PUBLIC_WS_URL` | Backend WebSocket URL (`ws://` locally, `wss://` in prod). |

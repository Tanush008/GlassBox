# Assignment Submission — Glassbox

> **Note to self before sending this:** the brief explicitly says to keep
> this in my own voice and not over-polish it. What's below is a
> complete first draft covering everything they asked for - read it
> through and rewrite the parts that don't sound like me, especially the
> Decision-making section. Don't just paste this in as-is.

---

## What I built and why

I built **Glassbox** - a small web app where you describe a code change
in plain English, and watch two things happen live: a context engine
picks which files in a demo codebase are actually relevant to your
request (and shows its work), and a three-agent pipeline (Planner →
Coder → Reviewer) plans, writes, and critiques the change, streaming
every step instead of just returning a final answer.

I chose this instead of something unrelated (a quiz app, a game) because
Superbrain's own three components - IDE, Agent, and a context-compressing
Architecture layer - are the actual problem space I'd be working in if I
got this role. Building a small, honest version of the same idea gave me
something more useful to say in the product-strategy questions below
than generic opinions would have: I ran into the same trade-offs
(context budget vs. completeness, how many review rounds before you cut
your losses) that a "real" version of this product has to make.

## Architecture and design

Two services:

- **Backend** (FastAPI + LangGraph + Groq API): a context engine
  that scores every file in a small demo repo against the request and
  packs the highest-scoring ones into a fixed token budget; a LangGraph
  state machine with three nodes (Planner, Coder, Reviewer) where the
  Reviewer can send the Coder back for another round with specific
  feedback; a WebSocket endpoint that streams the context decision and
  every agent step to the frontend as it happens.
- **Frontend** (Next.js + TypeScript + Tailwind): a file explorer for
  the demo repo, a live "context meter" showing relevance scores and
  token compression %, and a color-coded live trace of the three
  agents, ending in a diff view.

Full technical detail (why LangGraph, why keyword-based scoring instead
of embeddings, why the token counter is an estimate not a real
tokenizer, etc.) is in the repo's `README.md`, since it got long enough
that duplicating it here would just be noise. Short version: every
non-obvious choice was made to keep the demo self-contained, honest
about what it actually does, and reproducible for whoever reviews it -
not to maximize how impressive a single feature sounds.

## GitHub repository

`<TODO: paste your GitHub repo link here>`

## Deployment

`<TODO: paste your Vercel deployment link here>`

*(Note: the backend that powers the live agent runs is deployed
separately, since it needs a long-lived WebSocket connection that
doesn't fit Vercel's serverless model - the Vercel-hosted frontend talks
to it. Deployment instructions and the reasoning are in the README.)*

## Decision-making

The two decisions I'd actually want to talk through in the next round,
because they're the ones with real trade-offs rather than obvious
answers:

**1. Keyword-overlap scoring instead of an embedding-based retriever
for the context engine.** Embeddings would generalize better - matching
a request that says "credentials" to a file about "passwords" without
any shared word. But every embedding call is a network dependency, an
API key, and money and time, and it's a black box in exactly the way
this whole project is trying not to be. Since the entire point of
Glassbox is *showing* why a file was picked, being able to point at the
literal matched terms felt like the right trade for a demo, even though
I know it's the first thing I'd swap out for a real, larger codebase.

**2. Capping the Reviewer↔Coder loop instead of looping until approved.**
An uncapped "keep revising until the reviewer is happy" loop is a real
failure mode I've hit before in agent systems - a stubborn critic and a
coder that can't quite satisfy it will spin and burn API spend
indefinitely. I capped it at 2 rounds by default and made the UI honest
about which outcome happened ("Approved" vs. "Shipped after max
rounds") rather than hiding the difference. That felt more important
than a marginally higher approval rate.

---

## Product Strategy

### A. If I were building this product, what would I change or add next, and why?

The core claim - "60 to 80 percent token savings while keeping full
repo awareness" - has a trust problem baked in: users can't check the
second half of that sentence. If I were leading this product, my first
move wouldn't be a new capability, it'd be making the context engine's
decisions inspectable - literally showing which files got pulled into
context for a given turn, the way Glassbox does. Right now the user has
to take "full repo awareness" on faith, and the first time the agent
misses something obvious because a file got compressed out of context,
that faith is gone.

Right behind that: a way to pin a file into context, or exclude one,
instead of only ever accepting the engine's guess. The failure mode I'd
worry about most is a relevant file (a shared config, a schema, a style
guide) that keeps losing the relevance-scoring lottery turn after turn -
giving the user an override turns "the tool got it wrong" into "I told
it and it listened," which is a much better failure mode to be in.

### B. What major UI issues do I dislike, and how do they annoy current users?

I'll be upfront that I wasn't able to get meaningfully hands-on with
Superbrain itself in the time I had, so this is drawn from AI coding
tools generally rather than Superbrain specifically - I'd want to revise
this with real specifics once I'm actually using the product day to day.

The one that bothers me most across the category: agent output arriving
as one big diff at the end instead of a visible trace while it's
working. You genuinely can't tell if the agent is stuck, about to do
something you'd want to stop, or just thinking, until it's already
done. People end up reading a large diff after the fact instead of
steering the agent mid-task, which is a worse and more expensive way to
catch a mistake. That's the specific problem I tried to make a small
dent in with Glassbox's live trace.

Second: when an agent edits the wrong file because it misjudged repo
structure, there's usually no cheap way to say "not that one" - you
revert everything and re-prompt with more detail, which costs both
tokens and patience. And third: diff review inside a narrow chat-style
sidebar, without real syntax highlighting or inline comments, makes
reviewing a multi-file AI-written change genuinely harder than reviewing
the same change as a normal PR - right at the moment people most need
it to be easy, since that's when they're deciding whether to trust and
accept the code.

# Assignment Submission — Glassbox

## What I built and why

I built **Glassbox** — a small web app where you describe a code change in plain English, and then watch two things happen live: a context engine decides which files in a demo codebase are actually relevant to the request and shows why, while a three-agent pipeline (Planner → Coder → Reviewer) plans, writes, and critiques the change.

I chose this project because the problem is close to the one Superbrain is solving. Superbrain's product is built around understanding large repositories, managing context efficiently, and then using that understanding to make code changes safely. Building a smaller version of that gave me a way to think about the same trade-offs rather than answering the product questions only from the outside.

The main trade-off I ran into was that giving an agent more context is not automatically better. Too little context causes it to miss something important, but too much context increases cost and can make the reasoning less focused. I also found that adding more agent loops does not necessarily improve the result — sometimes it just creates more opportunities to spend tokens without getting meaningfully closer to a correct answer.

That was the main reason I wanted Glassbox to make those decisions visible instead of hiding everything behind a final answer.

## Architecture and design

Two services:

* **Backend** — FastAPI + LangGraph + Groq API. The context engine scores every file in a small demo repository against the user's request and packs the highest-scoring files into a fixed token budget. The LangGraph state machine has three nodes: Planner, Coder, and Reviewer. The Reviewer can send the work back to the Coder with specific feedback for another round. A WebSocket endpoint streams the context decisions and every agent step to the frontend as they happen.

* **Frontend** — Next.js + TypeScript + Tailwind. It has a file explorer for the demo repository, a live context meter showing relevance scores and estimated token compression, and a color-coded trace of the three agents, ending with a diff view.

I kept the implementation intentionally small and self-contained. For example, I used keyword-based relevance scoring rather than embeddings, and the token counter is an estimate rather than a model-specific tokenizer. Those are not claims that the demo is production-ready; they are deliberate choices that make the system understandable and reproducible.

The README contains the deeper technical reasoning behind those choices, including why I used LangGraph, why I chose keyword scoring for the demo, and where I would replace those decisions in a production system.

## GitHub repository

https://github.com/Tanush008/GlassBox

## Deployment

`<TODO: paste your Vercel deployment link here>`

The frontend is deployed on Vercel. The backend is deployed separately because the live agent workflow uses a long-lived WebSocket connection, which doesn't fit naturally into Vercel's serverless execution model. The README explains the deployment setup and why I made that split.

---

# Decision-making

The two decisions I would most want to talk through in the next round are the ones where I had to trade off one good property against another.

### 1. Keyword-overlap scoring instead of an embedding-based retriever

For the demo, I chose keyword overlap for the context engine.

An embedding-based retriever would be more capable. It could understand that a request about "credentials" might be relevant to a file that talks about "passwords" even when the exact words do not overlap.

But there was another requirement I cared about: **Glassbox should be able to show its reasoning.**

With keyword scoring, when a file is selected I can show the exact terms that caused it to score highly. That makes the context decision inspectable instead of presenting another black box.

The downside is that the approach does not generalize nearly as well as semantic retrieval, especially as repositories get larger and terminology becomes less predictable. So this is one of the first things I would change in a production version.

My next version would probably be a hybrid: semantic retrieval for better recall, combined with an inspectable relevance explanation and the ability for the developer to override the context engine.

That last part matters to me because a context engine should not become an invisible authority over what the agent is allowed to see.

### 2. Capping the Reviewer ↔ Coder loop

I deliberately capped the Reviewer → Coder loop at two rounds rather than letting the system continue until the Reviewer approves the change.

An unlimited loop sounds attractive because, in theory, the agents can keep refining the answer until it is correct. In practice, an agent system can get stuck in a cycle where the Reviewer keeps finding relatively small issues and the Coder keeps making small changes without converging.

That creates a worse failure mode than simply stopping: the system can spend a large amount of time and API budget without producing a meaningfully better result.

So I chose a fixed maximum and made the UI show which outcome happened:

* **Approved**
* **Shipped after max rounds**

I preferred making that limitation visible rather than pretending both outcomes represented the same level of confidence.

In a production system, I would make the loop adaptive rather than simply larger: use test failures, severity of reviewer feedback, and change magnitude to decide whether another round is actually worth the cost.

---

# Product Strategy

## A. If I were building this product, what would I change or add next, and why?

The first thing I would focus on is **making the context engine inspectable**.

Superbrain's core product claim is that TokenFold can reduce token usage substantially while maintaining repository awareness. That's a compelling idea, but the difficult part from a product perspective is not the token saving — it is proving that the compression did not remove something important.

If the agent gets a task wrong because an important file was compressed out of context, the user does not really care that the system saved tokens. They care that it missed the dependency that mattered.

So I would make context a first-class part of the product.

For every task, I would let the developer see something like:

```text
Files included
Files excluded
Why each file was selected
Estimated importance
What context was compressed
```

That gives the user a way to inspect the most important decision the system is making instead of having to trust the phrase "full repository awareness."

I would then add **context controls**:

* Pin a file into context
* Exclude a file
* Pin a directory
* Give a file higher priority
* Save context rules for the repository

For example, if a repository has a shared `schema`, `architecture.md`, or internal style guide that is relevant to almost every task, I should not have to hope that a relevance algorithm selects it every time.

The user should be able to say:

> "This is always important."

That changes the failure mode from *"the system ignored something important"* to *"the system followed the developer's explicit instruction."*

### The next thing I would build: repository intelligence beyond file retrieval

I think this is where Superbrain could become much more differentiated from a normal coding agent.

Instead of only thinking about "which files should I send to the model?", the product should maintain a more structured model of the repository:

```text
Repository
 ├── Architecture
 ├── Dependencies
 ├── Execution flow
 ├── Git history
 ├── Tests
 ├── Engineering conventions
 └── Known technical debt
```

Then a developer could ask:

> "If I change this authentication service, what else is likely to break?"

And the product could return:

```text
Potential impact:
- 4 services
- 12 API routes
- 18 tests
- 2 database models

Risk:
High

Recommended tests:
...
```

That is more useful to me than just generating code.

The long-term direction I would want is for Superbrain to become an **engineering intelligence layer**, not just another coding agent.

The model may change. The IDE may change. The coding agent may change.

The repository understanding and engineering memory should remain.

---

## B. What major UI issues do I dislike, and how do they annoy current users?

I want to be careful here because I wasn't able to spend enough time using Superbrain itself to claim that these are definitely current Superbrain UI bugs. The current product is also still in private beta. So these are the UI problems I see most often in AI coding tools, and the problems I would specifically look for when using Superbrain.

### 1. The user sees the result, but not enough of the reasoning

A common pattern is:

```text
Prompt
↓
Agent works
↓
Large diff appears
```

The problem is that the user doesn't see enough of the decisions happening in between.

If the agent chooses the wrong file, makes a questionable architectural assumption, or starts heading in the wrong direction, the developer often only discovers it when the work is already finished.

That's exactly the problem I was trying to address with Glassbox's live trace.

I would want Superbrain to make the process visible without overwhelming the developer:

```text
Understanding repository
↓
Relevant files selected
↓
Implementation plan
↓
Changes proposed
↓
Tests
↓
Reviewer feedback
```

The important part is not showing every internal thought. It's showing the **useful engineering decisions and evidence**.

### 2. Developers need cheap ways to correct the agent

Another problem is that when an agent chooses the wrong file or makes the wrong assumption, the correction loop can be expensive.

The current pattern in many tools is basically:

> stop → revert → explain the problem again → rerun

I would rather make correction part of the workflow.

For example:

> "Don't touch this file."

or

> "This service is read-only."

or

> "Always include `schema.prisma` for database-related tasks."

The agent should learn that constraint immediately and continue.

That makes the interaction feel more like steering an engineer than restarting a chatbot.

### 3. Reviewing AI-generated changes should be as good as reviewing a normal PR

The last issue is the review experience.

AI-generated changes can touch many files, so the point where the developer decides whether to trust the change is extremely important.

A narrow chat panel with a giant diff makes that harder.

I would want the review experience to show:

```text
Files changed
Why they changed
Dependency impact
Tests run
Tests passed
Reviewer concerns
Potential risk
```

Then the actual diff.

The goal should be to answer:

> **"Why should I trust this change?"**

rather than simply:

> **"What code did the agent generate?"**

That distinction is important to me because I think the long-term challenge for AI coding tools is not only generating code. It is helping developers make a confident decision about whether the generated change is actually safe.

---

# What I would measure

I would also add one product metric that I think is more meaningful than token savings alone:

**Successful changes per unit of context/cost.**

For example:

```text
Task success rate
Tokens used
Cost
Time to completion
Tests passed
Regression rate
Human acceptance rate
```

A context engine that uses 50% fewer tokens but causes developers to fix its mistakes manually is not necessarily better.

The real goal should be:

> **minimum useful context, maximum engineering correctness.**

That is the product problem I found most interesting while building Glassbox, and it is also the part of Superbrain I would be most interested in working on.

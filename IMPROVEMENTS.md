# Improvement log — the evolution of this project

This is a learning project, and this file is the *learning* made visible: every change I made, **why** I made it, and what it taught me — including the fixes, the tuning, the one bug that mattered, and the experiment that **didn't** improve the numbers. It's deliberately honest. If you want the polished overview, read the [README](./README.md); if you want my voice and reasoning, read the [WALKTHROUGH](./WALKTHROUGH.md); this file is the running ledger underneath both.

Each entry is **What → Why → Result / what I learned.** Dates and commit hashes are real (`git log`), so the trail is auditable.

| Date | Milestone | Commits |
|---|---|---|
| 2026-06-26 | First working build + readiness review & fixes | `df03980`, `db03e38`, `bf0debd` |
| 2026-06-26 | Learning docs (journey + reorg) | `93fd108`, `efb8dd4` |
| 2026-06-30 | Made the agent observable (live visualizer) | `214066a` |
| 2026-06-30 | Governance: multi-agent + structure + guardrails + logging | `c0e7d92` |
| 2026-06-30 | Configurable independent verifier (single-key) + docs | `2c0aa44` |
| 2026-06-30 | One-command setup (`.env.example` + dotenv) | `7b6783f` |

---

## 2026-06-26 · Readiness review, and the fixes it forced

I reviewed the project like I'd review a production service before publishing it. The audit found real problems — so the first "release" was mostly fixes. (These predate version control, so they landed together in the first real commit `db03e38`; the work itself was a review-then-fix pass.)

### Rebuilt the eval judge (33% → a real 67–80%)
- **What:** The LLM-as-judge graded with the *same* model that wrote the answer, demanded a literal match on *all* key facts, and answered a bare YES/NO. I changed it to **reason one sentence, then emit `VERDICT: YES/NO`**, grade *semantic* reflection (paraphrase counts), and pinned it to a **strong, independent model**. I also fixed the trajectory metric to only **hard-require live-data tools** (`get_metric`, `recent_deploys`, `search_logs`), since `get_runbook` is already satisfied by RAG.
- **Why:** The gate printed `BLOCKED` at 33%. Debugging it like a bad alert showed `tools=True`/`safe=True` almost everywhere — **the agent's answers were good; the judge was broken.** A wrong measurement is worse than no measurement.
- **Result / learned:** 33% → 67–80%. The headline lesson: *debug the measurement before you "fix" the system*, and never let a model grade its own work unchecked. I did **not** lower the gate to fake a pass.

### Added `requirements.txt`
- **What / Why:** There was none, and `mcp` wasn't installable — a fresh clone couldn't run the MCP server. **Result:** repo runs from a clean checkout.

### `run_tool` returns errors as the tool result
- **What:** Wrapped tool execution in `try/except`; a bad argument now returns `"error: …"` instead of raising.
- **Why:** The README *claimed* the model could recover from tool errors, but the code crashed — the docs over-promised. **Learned:** make the code match its own claims; the error text becomes the model's next observation, so it can self-correct.

### `search_logs` matches the log *level*, not just the message
- **What / Why:** A search for `"ERROR"` returned nothing because it only matched the `msg` field. Now it matches `level` too. **Learned:** a tool that silently can't find the obvious thing produces confident-but-empty answers.

### MCP server exposes all 5 tools (was 4)
- **What / Why:** `get_runbook` was missing, so the agent and the MCP surface disagreed. Now they're in sync.

### Reconciled the docs with reality
- **What:** Removed a fabricated `13/15 = 87% → GATE: OPEN` example and a stray absolute file path pasted into a doc.
- **Why:** The docs claimed a passing scorecard the project didn't have. **Learned (the rule for the whole project):** never publish a number you didn't measure.

### Repo hygiene
- **What / Why:** `git init`, a real `.gitignore` (`.venv`, `.env`, `__pycache__`, `.DS_Store`), and a proper top-level `README.md` so the project is cloneable and legible.

---

## 2026-06-26 · Made it a learning artifact, not a doc dump

- **What:** Wrote [`WALKTHROUGH.md`](./WALKTHROUGH.md) (the decision-by-decision journey, in my voice, including the "I audited my own project and it was broken" arc). Then removed the early `README_CONTENT_PACK.md` scaffolding note and moved the two teaching docs into `notes/`.
- **Why:** A root with five markdown files reads like a generated dump; a root of `README` + `WALKTHROUGH` + code with notes tucked away reads like a real project with a study trail.
- **Learned:** what makes a repo feel like a genuine journey is honest narrative + a clean structure — *not* faked commit history (which I explicitly chose not to do).

---

## 2026-06-30 · Made the agent observable — a live visualizer

- **What:** Added `viz/` — a dependency-free web app (stdlib HTTP + Server-Sent Events) that streams a run in real time: RAG → each model decision → every tool call with args + observation → the cited answer. Wired via a **non-breaking** optional `on_event` hook on the agent (defaults off, so the CLI and evals are untouched).
- **Why:** "It looked right when I tried it" isn't evidence. After years of staring at dashboards during incidents, building a *dashboard for the agent* was the obvious move — you can watch a cheap model take more steps (or go wrong) than a strong one on the same question.
- **Learned:** observability for an LLM app is just tracing applied to a new kind of system — and seeing the trajectory makes failure modes obvious.

---

## 2026-06-30 · Governance — multi-agent, structure, guardrails, logging

This was a big one, and the most instructive, because part of it **didn't do what I expected.**

### Opt-in multi-agent pipeline
- **What:** `ONCALL_MODE=multi` wraps the single agent in three roles: `triage (router) → investigator → verifier (actor→critic, one revision) → postmortem`. Default stays single-agent.
- **Why:** To demonstrate a real multi-agent pattern *without* faking it. Triage only short-circuits genuine out-of-scope questions, so it can't secretly strip the investigator's tools.

### Forced response structure
- **What / Why:** In governed mode the answer must carry labelled sections (`Diagnosis / Evidence / Recommended action / Approval`); a missing section triggers a revision. Predictable shape for an on-call tool.

### Configurable guardrails
- **What:** Safety policy moved into [`guardrails.json`](./guardrails.json) (allowed tools, required citations, required sections, forbidden "I-executed-a-destructive-action" phrases, mandatory approval language), enforced by `src/guardrails.py` on every answer.
- **Why:** Prompt = guidance; read-only tools = guarantee; an explicit, inspectable policy = the bit a reviewer can actually read and trust. Safety as config, not vibes.

### Full run logging
- **What / Why:** `src/trace.py` writes one JSONL per run to `logs/` — reasoning, every action + observation, verifier verdict, guardrail result, final answer. Observability for the agent itself; the basis for online evals later.

### The tuning fix that mattered
- **What:** The verifier first parsed its "issues" with a brittle string split, which often handed the reviser **near-empty feedback** — so the revision couldn't correct anything. Switched the verifier to emit tagged single-line fields (`ISSUES: / GROUNDED: / SAFE: / VERDICT:`) and parsed those.
- **Why / learned:** A critic is only as useful as the *actionable* feedback it passes downstream. The visible symptom ("revision didn't fix the answer") had its root cause one layer up (the parser starved the reviser). Classic: debug the pipe, not just the endpoint.

### The honest result (the part I'm most careful about)
- **What I measured:** Governed multi-agent mode held the gate at **12/15 = 80% (OPEN)** on Anthropic — **the same headline as single-agent. It did not raise the score.**
- **Why it didn't:** The verifier reliably *catches* the over-claim (the `payments` "rising → degraded" draft), but a single revision sometimes **over-corrects into hedging** that the strict judge also fails; and 15 cases is too few to detect a real delta.
- **Learned:** a critic tuned only to punish over-claiming pushes the actor toward useless "I can't be sure" answers — also wrong for on-call. **The multi-agent value here is governance and observability, not accuracy** — and I won't claim an accuracy win I didn't measure.

---

## 2026-06-30 · Made the verifier's independence real and honest

- **What:** The verifier/judge model is configurable (`JUDGE_PROVIDER` / `JUDGE_MODEL`) and works on a **single OpenRouter key** (point it at a different OpenRouter model). The pipeline emits a `verifier_info` event with an `independent` flag; if no independent model can be built it **falls back to the answering model and says so** — in the visualizer and the run log.
- **Why:** A verifier that runs on the same model as the answerer is self-grading — the same bias I designed the eval judge to avoid. If independence is lost, that should be *visible*, not hidden.
- **Learned:** trust properties (independence, provenance) are worth surfacing explicitly, not assuming.

## 2026-06-30 · One-command setup

- **What / Why:** Added [`.env.example`](./.env.example) documenting every variable (incl. the single-key judge block) and optional `.env` auto-load via `python-dotenv`, so `cp .env.example .env` + one key actually works. Removed friction for the next person (and future me).

---

## Open threads (what I'd do next, and why it's not done)

These are deliberately *not* fixed yet — an eval that only contains cases you pass isn't measuring anything. See the README's "Known failure modes" for the live failures.

1. **Give `get_metric` real thresholds** so "rising" means a meaningful change, not 180→200 ms. Biggest correctness win; root cause of the `payments` failures.
2. **Hybrid retrieval + reranking** to fix the keyword-RAG recall miss on the db-latency runbook.
3. **Recalibrate the verifier rubric** to penalise *both* over-claiming and unhelpful hedging, with a second revision budget — then re-measure.
4. **Bigger eval set** so a multi-agent accuracy delta would actually be detectable.
5. **Online evals** — sample real runs from the JSONL logs and grade them; treat evals as a living dataset.

---

*Principle running through all of it: ground it, constrain its blast radius, and measure it honestly — and write down what was actually true, including when a change didn't help.*

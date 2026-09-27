# Assumption Zero × IBM Bob 2.0

Assumption Zero is built around the workflow a Bob-style full-repository
coding agent is uniquely good at: understanding an entire codebase's
architecture, running specialized analyses across many files at once, and
then verifying a fix by actually executing code — not just proposing a
diff and hoping.

This directory documents exactly how Bob participates in the Assumption
Zero workflow during the hackathon, and why a single-file/single-function
chatbot cannot do this job.

## Why this problem needs Bob, not a chatbot

A person pasting one file into a chat assistant can catch, at best, one
layer's assumption. The entire premise of Assumption Zero is that **no
single file is wrong on its own** — `schemas.py` alone just looks like an
ordinary required field. The contradiction only becomes visible when you
hold `ApplicationForm.tsx`, `schemas.py`, `migration.sql`, and
`test_applications.py` in view **at the same time**, next to `POLICY.md`,
and notice they all encode the same silent assumption independently.

That's exactly Bob's mode: full-repository awareness, planning across many
files, running specialized sub-agents in parallel, and then verifying with
real execution (tests, replayed requests) instead of stopping at a
suggestion.

## The five phases, mapped to Bob's modes

| Assumption Zero phase | Bob mode | What happens |
|---|---|---|
| Read `POLICY.md`, understand repo layout | **Plan mode** | Bob reads the policy document and the repository tree, identifies the layers likely to encode human assumptions (forms, schemas, migrations, tests, network handling), and produces the analysis plan documented in `bob/workflows/`. |
| Run the 5 specialized agents | **Agent mode + parallel agents** | Bob dispatches independent analysis passes — one per layer — that can run concurrently because they touch disjoint files. `analyzer/agents/*.py` is the concrete, standalone implementation of exactly this workflow (see `bob/prompts/agent_prompts.md` for the prompt each sub-agent would run under if driven directly by Bob rather than by the bundled Python agents). |
| Build the Assumption Graph, trace contradictions | **Agent mode (synthesis)** | Bob correlates findings across the five parallel passes into the cross-layer graph in `analyzer/assumption_graph.py`. |
| Generate + apply a repair, run tests, replay Noor | **Verification** | Bob doesn't stop at "here's a suggested diff." It edits the real files (`analyzer/repair.py`), re-runs the real pytest suite, and re-executes the real Noor journey against the live application (`analyzer/verifier.py`) — proof, not a claim. |
| Produce the final report | **Documentation capability** | Bob assembles the Human Compatibility Score, the evidence trail, and the before/after verification into the `reports/` output described below. |

## Running this analysis inside Bob during the hackathon

Because Bob's own external APIs were not available to call programmatically
during this build, Assumption Zero ships **fully self-contained**: every
phase above already runs as ordinary, inspectable Python
(`analyzer/orchestrator.py`, `analyzer/repair.py`, `analyzer/verifier.py`)
that a judge can run directly with `python -m analyzer.cli demo`.

The Bob-native path is layered on top, not faked underneath:

1. Open this repository in Bob.
2. Feed Bob the plan in `bob/workflows/analysis-workflow.md` — it tells
   Bob to read `demo_target/POLICY.md`, then dispatch the five agent
   prompts in `bob/prompts/agent_prompts.md` against `demo_target/` in
   parallel, using the exact same JSON finding schema the Python agents
   already use (`analyzer/models.py::Finding`), so Bob's output is a
   drop-in replacement for (or supplement to) `analyzer/orchestrator.py`'s
   output.
3. Bob's findings can be merged into `analyzer/orchestrator.py`'s output
   via the same `Finding` schema, so the dashboard, graph, and scoring
   engine all work identically whether a finding came from the bundled
   static analyzers or from a Bob agent run.
4. `bob/workflows/repair-workflow.md` documents the equivalent Plan →
   Apply → Verify loop for repairs, matching `analyzer/repair.py` and
   `analyzer/verifier.py` 1:1.

See `bob/sample-session.md` for a transcript-style walkthrough of what this
looks like end to end.

## AI Mode vs Demo Mode

Assumption Zero supports two modes (see `analyzer/requirements.py`,
`analyzer/ai_mode.py`, and the root `README.md` → "AI Architecture"):

- **Demo mode** (default, no API key required): deterministic static
  analysis + real code execution, exactly what `analyzer/agents/*.py` do,
  plus a regex-based `### REQ-n` parser for `POLICY.md`. This is what
  guarantees the hackathon demo never breaks — nothing in this path ever
  calls an external API.
- **AI mode** (optional, real working code — not a placeholder): if
  `ANTHROPIC_API_KEY` is set, `analyzer/ai_mode.py::extract_requirements_ai`
  calls the Anthropic API to interpret an *arbitrary* policy document that
  doesn't use the `### REQ-n` heading convention, extracting the same
  structured requirement schema an LLM-backed agent would. This is the
  path used for generalizing beyond the one bundled demo target; the
  Frontend/Backend/Database/Test/Resilience agents themselves remain
  deterministic either way. This is also the mode a Bob-native run
  (`bob/prompts/agent_prompts.md`) uses for the five specialized agents
  directly, when Bob is doing the analysis instead of the bundled Python
  agents.

`extract_requirements_ai` fails closed on any error — missing key, bad
key, network failure, malformed response — and returns `None`, which
`extract_requirements` treats identically to "AI mode not configured."
The demo's own `POLICY.md` always matches the regex parser first, so this
fallback path is never exercised during a normal demo run regardless of
whether a key is configured.

Both modes emit the same `Finding`/`Requirement` schema, so the rest of
the pipeline (graph, scoring, repair, dashboard) is completely agnostic to
which mode produced a given finding.

## For your hackathon submission

The lablab.ai submission form requires evidence that IBM Bob 2.0 was
actually used, not just architected for — specifically "IBM Bob task
session summary screenshots from each team member." That evidence has to
come from a real Bob session you run, which this repository can't create
for you. Concretely, before you submit:

1. **Get your IBM Bob 2.0 access** (from your hackathon registration
   email) and open it against this repository or your fork of it.
2. **Run the actual workflow** in `bob/workflows/analysis-workflow.md`
   and `bob/workflows/repair-workflow.md`, using the five prompts in
   `bob/prompts/agent_prompts.md`. This is designed to exercise the exact
   capabilities the challenge asks you to leverage:
   - **Document understanding** — Bob reading `demo_target/POLICY.md`
     and extracting the REQ-1..REQ-5 requirements from it.
   - **Agent mode + parallel subagents** — the five specialized agents
     (Frontend, Backend/API, Database, Test, Resilience) dispatched
     concurrently against disjoint parts of `demo_target/`.
   - **Verification, not just generation** — Bob applying a repair,
     running the real `pytest` suite, and re-replaying the Noor journey
     to prove the fix, rather than stopping at a suggested diff.
3. **Screenshot each stage** and save them under
   `bob/session-screenshots/` (see the README there for exact naming and
   what's most convincing to capture).
4. **Update the IBM Bob Usage Statement** in `SUBMISSION.md` at the repo
   root with what you actually observed Bob do, once you've run it for
   real — the draft there is written from this repository's own
   architecture and is ready to edit, not to submit verbatim without
   having actually run the session it describes.

Judges weight "Application of Technology" specifically on **clear
application of IBM Bob 2.0** — real task sessions are what separates a
documented integration from a demonstrated one.

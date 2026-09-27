# Workflow: Full Repository Analysis

This is the task list Bob would execute in **Plan mode**, then **Agent
mode**, to produce the same output as `analyzer/orchestrator.py`.

## Plan mode

1. Open `demo_target/POLICY.md`. Extract each `### REQ-n` requirement into
   a structured list (id, title, binding statement). This matches
   `analyzer/requirements.py::extract_requirements`.
2. Enumerate the repository tree under `demo_target/`:
   - `frontend/` — UI form(s)
   - `backend/` — API routes, request/response schemas, DB migration
   - `tests/` — regression suite
3. For each requirement, identify which layers are *plausible surfaces*
   for a contradiction (a surname requirement could live in a form field,
   a schema validator, a DB constraint, or a missing test — never assume
   only one).
4. Produce a task list: one task per (agent, layer) pair, all
   independent of each other (they read disjoint files), so they are
   safe to dispatch concurrently.

## Agent mode — parallel dispatch

Dispatch the five agents from `bob/prompts/agent_prompts.md` concurrently:

```
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Frontend Agent   │   │ Backend Agent    │   │ Database Agent   │
│ reads frontend/  │   │ reads backend/   │   │ reads migration  │
└─────────────────┘   └─────────────────┘   └─────────────────┘
┌─────────────────┐   ┌─────────────────┐
│ Test Agent       │   │ Resilience Agent │
│ reads tests/     │   │ EXECUTES the app │
└─────────────────┘   └─────────────────┘
```

Each agent returns a JSON array of `Finding` objects (schema in
`bob/prompts/agent_prompts.md`). This is exactly what
`analyzer/agents/*.py::run()` return today as `AgentReport.findings`.

## Synthesis

5. Merge all findings into a single list.
6. Group findings by `human_requirement` to build the Assumption Graph
   (`analyzer/assumption_graph.py::build_graph`) — one requirement node,
   fanning out to one node per layer that independently encodes the same
   assumption.
7. Generate the counterexample persona (Noor) from the requirements that
   have findings, and replay it against the live application
   (`analyzer/counterexample.py::run_journey`).
8. Compute the Human Compatibility Score
   (`analyzer/scoring.py::compute_score`) from the merged findings plus the
   journey result.

## Output

Emit the same top-level JSON shape `analyzer/orchestrator.py::run_full_analysis`
returns: `requirements`, `agent_reports`, `findings`, `graph`, `journey`,
`score`. The dashboard (`apps/web/index.html`) and API (`apps/api/main.py`)
do not
need to know or care whether this JSON came from the bundled Python agents
or from a live Bob agent run — same schema in, same UI out.

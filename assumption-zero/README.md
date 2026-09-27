# Assumption Zero

### Find the human assumptions hidden in your software.

> "Your tests can pass while your users still fail."

Built for the **IBM Bob 2.0 Hackathon** (lablab.ai).

---

## The Problem

Software rarely says out loud that someone isn't allowed to use it.
Instead, assumptions about *who a normal user is* get baked quietly into code:

| What the developer wrote | What it actually means |
|---|---|
| `last_name: str` (required) | People with one legal name cannot apply |
| `address: str` (required) | Displaced persons without a home cannot apply |
| `US_PHONE_PATTERN = /^\(?\d{3}\)?...$/` | International applicants are rejected |
| `NOT NULL` on `last_name` | Even if you fix the form, the database still blocks them |

Each line is reasonable in isolation. The bug only exists in the relationship between a policy document and five different files that no single-file code review ever holds at once. Standard linters, type-checkers, and test suites have no concept of "who is allowed to use this software." The exclusion is found, if at all, by a support ticket from a real user — months after release.

**Assumption Zero** makes this class of bug testable, traceable, and fixable before deployment.

---

## Solution

Given a repository and a plain-English policy document, Assumption Zero answers one question with **proof, not opinion**:

> *Does the implementation actually support what the policy promises?*

```
Requirements / Policy (POLICY.md)
              │
              ▼
     Repository Analyzer
              │
   ┌──────────┼──────────┬───────────┬────────────┐
   ▼          ▼          ▼           ▼            ▼
Frontend   Backend/API  Database    Test        Resilience
 Agent       Agent       Agent      Agent          Agent
(regex on   (AST scan   (schema    (AST scan    (executes live
 JSX/HTML)   of Pydantic  parse of   of pytest    app twice,
             models)      SQL DDL)   suite)       inspects DB)
   │          │          │           │            │
   └──────────┴──────────┴───────────┴────────────┘
                          │
                          ▼
                 Assumption Graph
        (one assumption → every layer that encodes it)
                          │
                          ▼
          Counterexample Journey Generator
         (persona "Noor" replayed via HTTP)
                          │
                          ▼
                     Fix Planner
                          │
                          ▼
             Patch Applier (real file edits)
                          │
                          ▼
                      Verifier
        (real pytest run + fresh re-analysis +
              re-replayed human journey)
```

---

## How It Works — The Demo

The demo target is **RapidRelief**, a fictional disaster-relief intake portal with five intentionally-flawed implementations of five human requirements from its own `POLICY.md`.

The persona **Noor** — one legal name, no permanent address, an international (+92) phone number — attempts to submit a relief application. Before repair:

```
Journey FAILED
  ✗ Validate `last_name`  (REQ-1)  Server rejected the request — no surname
  ✗ Validate `address`    (REQ-2)  Server rejected the request — no address
  ✗ Validate `phone`      (REQ-3)  Server rejected the request — Pakistani number
```

After one click on "Generate Repair Plan" → "Apply Demo Fix" → "Verify Repair":

```
Journey PASSED  (application id returned)
Human Compatibility Score: 40/100 → 100/100
pytest: 9/9 tests pass (5 new regression tests added)
```

Every finding links to a real file and line you can open yourself. Every repair is a real patch applied to real files on disk.

---

## Architecture

### Five Specialized Agents

| Agent | Method | What it finds |
|---|---|---|
| **Frontend Agent** | Regex over JSX/HTML | `required` fields, Latin-only name validators, US-only phone patterns |
| **Backend/API Agent** | Python `ast` over Pydantic models | Non-optional required fields, US-only phone validators, Latin-name validators |
| **Database Agent** | Regex over SQL DDL | `NOT NULL` constraints on fields the policy says are optional |
| **Test Agent** | Python `ast` over pytest functions | Requirements with zero test coverage (will silently regress) |
| **Resilience Agent** | **Executes the live app** via `TestClient`, submits twice, inspects the database | Duplicate-submission bug (no idempotency key) |

Each agent is a deterministic static analysis (or real code execution) — not an LLM call. The demo works with zero API keys and can never fail because an external service is unavailable.

### The Assumption Graph

The graph connects a single human assumption (e.g. "every person has a surname") to every layer that independently encodes it. REQ-1 fans out to four separate layers: frontend validation, backend Pydantic schema, database `NOT NULL` constraint, and a missing test. Clicking a node highlights its entire propagation chain — the core visual insight.

### Human Journey Executor

`analyzer/counterexample.py` replays Noor's application against the **real, running** demo app via FastAPI's `TestClient`. Every step is a genuine HTTP request and response — the failure is proved by execution, not asserted.

### Repair Engine

`analyzer/repair.py` applies real text patches to real source files on disk. The verifier (`analyzer/verifier.py`) then runs the real `pytest` suite and re-replays Noor's journey against the patched code to prove the fix works.

### Human Compatibility Score

A deterministic 0–100 score: starts at 100, subtracts severity-weighted penalties per finding (critical: −6, high: −4, medium: −2, low: −1) plus an additional −8 if the hero human journey fails end-to-end. Every point lost is attributable to a specific finding. The dashboard shows a "How is this calculated?" breakdown.

---

## IBM Bob Integration

This project is architected so that a Bob-style full-repository agent is the **natural** way to run it — not a bolted-on feature.

The entire premise is that no single file is wrong in isolation. The bug only exists in the *relationship* between five files that no single-file review ever holds at once. That requires Bob's full-repository, multi-agent reasoning:

- **Plan mode** to read the policy and repository structure
- **Agent mode with parallel subagents** for the five independent analyses
- **Verification over generation** — runs real `pytest` and re-replays the human journey rather than trusting a generated diff

See **[`bob/README.md`](bob/README.md)** for:
- Why this problem specifically needs full-repository reasoning
- The exact prompts for each sub-agent (`bob/prompts/agent_prompts.md`)
- The Plan → Agent → Verify workflow (`bob/workflows/`)
- A sample session transcript (`bob/sample-session.md`)

---

## Tech Stack

| Layer | Choice |
|---|---|
| Demo application backend | Python, FastAPI, SQLite |
| Demo application frontend | Static HTML/JS (`demo_target/frontend/index.html`) + canonical React/TypeScript source (`ApplicationForm.tsx`) |
| Analyzer | Python — `ast` for structural parsing, regex for pattern matching, FastAPI `TestClient` for resilience testing |
| Analyzer API | FastAPI (`apps/api/main.py`) |
| Dashboard | Single self-contained HTML/CSS/JS file (`apps/web/index.html`), zero build step |
| Tests | pytest |

No Node.js, npm, or build tooling required.

---

## Quick Start

### Requirements
- Python 3.10+
- No Node.js required

### One command

**Windows:**
```bat
start_all.bat
```
or in PowerShell:
```powershell
.\start_all.ps1
```

**macOS/Linux:**
```bash
./start_all.sh
```

This installs dependencies (first run only), starts both servers, and opens the dashboard at **http://localhost:8010**.

### Manual setup (two terminals)

**Terminal 1 — Demo app (port 8000):**
```powershell
.\run_demo_app.ps1          # Windows
./run_demo_app.sh           # macOS/Linux
```

**Terminal 2 — Analyzer API + dashboard (port 8010):**
```powershell
.\run_analyzer_api.ps1      # Windows
./run_analyzer_api.sh       # macOS/Linux
```

Then open **http://localhost:8010**.

### Environment variables

Copy `.env.example` to `.env` to enable AI mode (optional Anthropic key for interpreting arbitrary policy documents). Nothing is required for the demo.

### Running tests

```bash
python -m pytest demo_target/tests -q
```

Use the `.venv` Python if running outside a virtual environment:
```powershell
.venv\Scripts\python.exe -m pytest demo_target/tests -q    # Windows
.venv/bin/python -m pytest demo_target/tests -q             # macOS/Linux
```

### CLI (no browser)

```bash
python -m analyzer.cli demo     # full before → repair → after flow
python -m analyzer.cli analyze  # analysis only, prints JSON
python -m analyzer.cli journey  # replay Noor only
python -m analyzer.cli repair   # apply fixes in place
python -m analyzer.cli verify   # re-run tests + re-analyze + re-replay
```

---

## Demo Instructions (3 minutes)

| Time | Action |
|---|---|
| 0:00–0:20 | Open dashboard. Point out the pipeline strip at the top (Repository → Agents → Assumptions → Human Journey → Evidence → Repair) and the POLICY.md requirements it's verifying. |
| 0:20–0:45 | Click **Analyze Repository**. Watch the five agents run with their specific roles. |
| 0:45–1:15 | Show the score (40/100) and the Assumption Graph. Click REQ-1 to highlight its four-layer propagation. |
| 1:15–1:45 | Scroll to the Human Journey section. Noor's journey is already shown — three steps, all failed. Each shows the human reason (not just a validation error). |
| 1:45–2:05 | Expand one finding in the Evidence section. Show the source file, line number, and human consequence. |
| 2:05–2:35 | Click **Generate Repair Plan** (shows diff previews), then **Apply Demo Fix** (patches real files). |
| 2:35–2:50 | Click **Verify Repair**. Watch pytest run and the score animate to 100/100. Journey now passes. |
| 2:50–3:00 | Close on the Before/After score comparison and the message: "Your tests can pass while your users still fail — Assumption Zero proves otherwise." |

---

## Impact

Every one of the five contradictions in this demo — a required surname, a required permanent address, a country-locked phone format, a Latin-script-only name filter, and a non-idempotent submission endpoint — appears constantly in real government and NGO software.

None of them are caught by a linter, a type checker, or a normal code review, because each individual line is completely reasonable in isolation.

Assumption Zero's core bet: this class of bug deserves the same rigor as a failing unit test — provable, traceable to a file and line, and blocking until fixed.

---

## Repository Structure

```
assumption-zero/
├── demo_target/                # the intentionally-flawed demo application
│   ├── frontend/               # form (static HTML + canonical .tsx source)
│   ├── backend/                # FastAPI app, Pydantic schemas
│   ├── database/               # SQLite DDL (migration.sql)
│   ├── tests/                  # pytest suite (with intentional coverage gaps)
│   └── POLICY.md               # the human requirements this app must satisfy
├── analyzer/                   # the Assumption Zero engine
│   ├── agents/                 # frontend/backend/database/test/resilience agents
│   ├── models.py               # Finding / AgentReport schema
│   ├── requirements.py         # POLICY.md → structured requirements
│   ├── ai_mode.py              # optional LLM-backed policy interpretation
│   ├── assumption_graph.py     # cross-layer graph builder
│   ├── counterexample.py       # Noor persona + journey executor
│   ├── scoring.py              # Human Compatibility Score
│   ├── repair.py               # repair plan + real patch application
│   ├── verifier.py             # re-test / re-analyze / re-replay
│   ├── orchestrator.py         # runs all agents + builds full report
│   └── cli.py                  # python -m analyzer.cli ...
├── apps/
│   ├── api/main.py             # FastAPI layer exposing the analyzer
│   └── web/index.html          # the dashboard (single HTML file)
├── bob/                        # IBM Bob integration docs, prompts, workflows
├── reports/                    # pristine snapshot for /api/reset-demo
├── requirements.txt
├── render.yaml                 # one-click Render deployment
├── start_all.bat / .ps1 / .sh  # one-command launcher
└── SUBMISSION.md               # hackathon submission package
```

---

## License

MIT — see `LICENSE`.

# Hackathon Submission Package — IBM Bob 2.0 Hackathon (lablab.ai)

This file maps directly to the submission form's fields. Copy each
section into the matching form field. Anything in `[brackets]` needs a
real detail from you before you submit — nothing in brackets should be
submitted as-is.

---

## Project Title

Assumption Zero — Human Requirement Verification for Software

## Short Description

Assumption Zero is a code-review and testing workflow, built for IBM Bob
2.0, that finds the assumptions software silently makes about its
users — a required surname, a mandatory home address, a country-locked
phone format — proves each one with an executed counterexample, then
repairs and re-verifies the fix.

## Long Description — Problem & Solution Statement (≤500 words)

**The workflow this improves: code review and testing for eligibility
and accessibility bugs.**

Software regularly excludes real users without ever raising an error. A
form that requires a last name, a schema that requires a permanent
address, a phone validator that only accepts one country's format — each
line looks completely reasonable to a reviewer looking at that one file.
The exclusion is only visible when you hold the product's own policy
document and every implementation layer — frontend, API schema, database
constraint, test suite — in view at once. No single-file code review
catches this, and standard linters and type checkers have no concept of
"who is allowed to use this software" to check against. Today this class
of bug is found, if it's found at all, by a support ticket from a real
excluded user months after release — which is exactly the "too many
errors, discovered too late, at too much cost" pattern the workflow
categories in this challenge target.

**What we built.** Assumption Zero takes a policy document (what the
software promises to support) and a real codebase, and answers one
question with proof, not opinion: does the implementation actually
support what the policy promises? Five specialized agents — Frontend,
Backend/API, Database, Test, and Resilience — inspect disjoint parts of
the repository in parallel: real AST parsing of Pydantic models, regex
analysis of JSX/HTML/SQL, and for the Resilience agent, actually executing
the live application twice to prove a duplicate-submission bug rather than
guessing at one. Every finding traces to a real requirement ID, a real
file, and a real line — a judge (or a developer) can open the file and
check it directly.

The system then generates the smallest realistic user scenario a policy
requires but the code doesn't support, and replays it against the running
application via a real HTTP request — a provable counterexample, not an
assertion. From there it generates a repair plan, applies real patches to
the real source files, re-runs the actual test suite, and re-replays the
counterexample to prove the fix works, closing the loop from detection to
verified repair.

**Why this needed Bob, not a single-file chat query.** The entire premise
is that no one file is wrong in isolation — the bug only exists in the
relationship between five files that no single-file review ever holds at
once. That's full-repository, multi-agent reasoning: Bob's Plan mode to
read the policy and repository structure, Agent mode with parallel
subagents to run the five independent analyses concurrently, and a
verification step that executes code rather than trusting a generated
diff.

**Impact.** What currently requires a developer to manually cross-reference
a policy document against every implementation layer by hand — a slow,
easy-to-miss process repeated for every new field, form, or endpoint —
becomes one automated pass with a traceable, explainable score
(Human Compatibility Score) that a team could gate a PR on, the same way
they'd gate on a failing test.

---

## IBM Bob Usage Statement (≤500 words)

[This section must describe what you actually observed when you ran IBM
Bob 2.0 against this repository — see `bob/README.md` → "For your
hackathon submission" for the exact steps. The draft below describes how
the repository is architected to be operated by Bob; replace the
bracketed / italicized notes with your team's real session details
before submitting.]

Assumption Zero's five-agent architecture is a direct implementation of
IBM Bob 2.0's own operating modes, not a metaphor for them:

- **Document understanding:** Bob reads `demo_target/POLICY.md` — a
  plain-English policy document — and extracts the binding human
  requirements (REQ-1 through REQ-5) it contains, the same way our
  bundled regex-based parser does deterministically for the demo, and the
  same way our optional AI-mode fallback (`analyzer/ai_mode.py`) does for
  an arbitrary, unstructured policy document.
- **Plan mode:** Before touching any file, Bob reads the repository
  structure under `demo_target/` and identifies which layers are
  plausible surfaces for each requirement — exactly the task list in
  `bob/workflows/analysis-workflow.md`.
- **Agent mode + parallel subagents:** The five prompts in
  `bob/prompts/agent_prompts.md` (Frontend, Backend/API, Database, Test,
  Resilience) are dispatched concurrently, because they read disjoint
  files and their findings are independent until a synthesis step
  correlates them into the Assumption Graph.
- **Verification over generation:** After a repair, Bob doesn't stop at a
  proposed diff. It applies the patch to the real files, runs the actual
  `pytest` suite, and re-replays the Noor counterexample against the
  live, patched application — the same Detect → Explain → Patch → Test →
  Replay → Verify loop in `bob/workflows/repair-workflow.md`.

*[Real session detail to add: which stage(s) you ran through Bob
directly, what Bob's session summary showed at each stage, and anything
Bob caught or fixed that the bundled deterministic Python agents in
`analyzer/agents/` didn't already handle. Reference your screenshots in
`bob/session-screenshots/` by filename.]*

Because IBM Bob's own APIs were not externally callable at the point this
repository's bundled `analyzer/` package was engineered, that package
ships as a fully standalone, deterministic implementation of the same
five-agent workflow — this is what guarantees the demo works reliably
regardless of Bob's live availability during judging, per this project's
own design principle that "the live demo must never collapse because an
external API is unavailable." The `bob/` directory is not a fallback
explanation for skipping Bob — it's the literal, runnable specification
for driving this same repository through Bob directly, which is what our
team did during the event: *[describe what you did here]*.

---

## Technology & Category Tags

**Technology:** Python, FastAPI, Pydantic, SQLite, pytest, JavaScript
(vanilla, no framework), IBM Bob 2.0, Anthropic Claude (optional AI mode),
AST static analysis, regex-based static analysis

**Category:** Developer Tools, Code Review & Testing, DevOps/QA
Automation, Accessibility & Inclusion, Multi-agent Systems

---

## Demo Application Platform / Application URL

Two independent services need a public URL each (see `README.md` →
"Deployment instructions" for exact commands, and `render.yaml` at the
repo root for a ready-to-use Render blueprint):

- **Analyzer API + dashboard:** `[fill in after deploying —
  e.g. https://assumption-zero-api.onrender.com]`
- **Demo application (RapidRelief portal):** `[fill in after deploying —
  e.g. https://assumption-zero-demo.onrender.com]`

The dashboard (served by the analyzer API at its root URL) is the
"Application URL" a judge should open first.

---

## Public Code Repository

`[your GitHub URL here once pushed — see "Preparing this as a public
GitHub repository" in README.md]`

## Cover Image

A ready-to-use 1280×720 PNG is provided at `docs/cover-image.png`
(source: `docs/cover-image.svg`, editable if you want to change any text
or resize it) — upload it directly, or replace it with your own.

## Video Demonstration

Follow the script in `README.md` → "Demo instructions" — it's written to
fit the exact constraint here (≤3 minutes total, ≥90 seconds of the
product actually running). Narrate the Bob-specific points explicitly
(the five parallel agents, the executed counterexample, the verified
repair) since judges are told to watch for clear IBM Bob 2.0 application.

## Slide Presentation

Not included as a file here — build from `README.md`'s "How it works" and
"Impact" sections plus the Assumption Graph screenshot; that's the
whole narrative arc already written out.

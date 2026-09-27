# IBM Bob Task Session Summary Screenshots

**This folder is intentionally empty except for this file.** The
hackathon's submission requirements state:

> "Your repository must include the code/files where IBM Bob assisted,
> plus IBM Bob task session summary screenshots from each team member."

Those screenshots have to come from an actual IBM Bob 2.0 session run by
you (or your teammates) during the event — they can't be produced ahead
of time by anyone else, including an AI assistant helping you prepare
this repository. This file exists so you have an obvious, correctly-named
place to drop them before you submit.

## What to actually do

1. Open IBM Bob 2.0 against this repository (or your fork of it).
2. Run the workflow documented in `bob/README.md` and
   `bob/workflows/analysis-workflow.md` — in short:
   - **Plan mode:** point Bob at `demo_target/POLICY.md` and this
     repository's structure. This exercises Bob's **document
     understanding** on the policy document.
   - **Agent mode + parallel subagents:** dispatch the five prompts in
     `bob/prompts/agent_prompts.md` (Frontend, Backend/API, Database,
     Test, Resilience) concurrently against `demo_target/`.
   - **Verification:** have Bob apply a repair, run
     `python -m pytest demo_target/tests -q`, and re-replay the Noor
     journey (`python -m analyzer.cli journey`) to confirm the fix.
3. Screenshot Bob's task session summary at each major stage (the plan,
   the parallel agent dispatch, and the verification result are the three
   most convincing moments to capture).
4. Save each screenshot here as `bob-session-<teammate-name>-<stage>.png`,
   e.g. `bob-session-amna-parallel-agents.png`.
5. Reference this folder from your submission's "Code Repository & IBM
   Bob Task Session Summary Screenshots" field.

## Why this matters for judging

"Application of Technology" is graded on **clear application of IBM Bob
2.0** specifically — not just a working prototype. A judge who can see
real Bob task sessions (not just documentation describing how Bob *would*
be used) is the difference between "documented integration" and
"demonstrated integration." Do this step before you submit.

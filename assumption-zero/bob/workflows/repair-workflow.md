# Workflow: Repair & Verification

This is the Detect → Explain → Generate patch → Apply patch → Run tests →
Replay journey → Verify loop, as Bob would run it, mirroring
`analyzer/repair.py` and `analyzer/verifier.py`.

## 1. Detect

Findings already produced by `bob/workflows/analysis-workflow.md`. Group
by `layer` so each patch touches one coherent concern.

## 2. Explain

For each finding, Bob restates `why_it_conflicts` and `recommended_fix` in
the repair plan shown to the user (`GET /api/repair-plan` →
`analyzer/repair.py::generate_plan`).

## 3. Generate patch

For each layer, Bob proposes a concrete text edit:

- **frontend** — remove `required` from surname/address inputs; replace
  the US-only phone regex with an E.164-compatible pattern.
- **backend** — change `last_name`/`address` from `str` to
  `Optional[str] = None`; drop the validators that reject empty values;
  replace the US phone validator with an international one.
- **database** — migrate the `last_name`/`address` columns to be nullable.
- **tests** — add regression tests for: no-surname applicant, no-address
  applicant, international phone number, and idempotent resubmission.
- **resilience** — accept an `Idempotency-Key` header on the submission
  endpoint; if a row already exists for that key, return it instead of
  inserting a duplicate.

## 4. Apply patch

Bob writes the edits directly to the real files in `demo_target/`. This is
not a simulated diff — `analyzer/repair.py::apply_all_fixes` performs
exactly this today as ordinary file I/O, so a judge can open the files
before/after and see a real, plain-text change.

## 5. Run tests

Execute `python -m pytest demo_target/tests -q` against the patched code
(`analyzer/verifier.py::run_pytest`). If tests fail, Bob does not claim
success — it reports the failing output and stops.

## 6. Replay journey

Re-run the Noor persona (`analyzer/counterexample.py::run_journey`)
against the now-patched, live application. This is the same function used
for the "before" run — nothing about the journey logic is special-cased
for "after."

## 7. Verify

Re-run the full five-agent analysis against the current (patched) files —
fresh reads, fresh execution, no caching of the "before" findings
(`analyzer/verifier.py::verify_repair`). Recompute the Human Compatibility
Score. The delta between before/after is only ever computed from two
independently-run analyses, never asserted directly.

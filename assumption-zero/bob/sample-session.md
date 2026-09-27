# Sample Bob Session

A transcript-style walkthrough of what running Assumption Zero's workflow
inside Bob looks like end to end. (Produced from an actual run of the
bundled `python -m analyzer.cli demo` — the numbers below are real output,
not illustrative placeholders.)

---

**Operator:** Analyze `demo_target/` against `demo_target/POLICY.md`.

**Bob (Plan mode):**
> Read POLICY.md — 5 binding requirements (REQ-1..REQ-5). Repository has
> four analyzable layers under `demo_target/`: `frontend/`, `backend/`,
> `database/`, `tests/`. Dispatching 5 parallel agents: Frontend,
> Backend/API, Database, Test, Resilience. Resilience agent will execute
> the live application to test retry behavior rather than infer it
> statically.

**Bob (Agent mode — parallel):**
```
Frontend Agent    -> scanned 2 frontend source file(s)               -> 3 findings
Backend/API Agent -> scanned 5 endpoint(s), 2 schema model(s)        -> 4 findings
Database Agent    -> scanned schema with 7 NOT NULL constraint(s)    -> 2 findings
Test Agent        -> inspected 4 test(s) across 1 file                -> 5 coverage gaps
Resilience Agent  -> executed 2x identical submission via TestClient -> 1 finding
```

**Bob (synthesis):**
> 15 findings total, spanning REQ-1 (surname), REQ-2 (address), REQ-3
> (phone), REQ-4 (resilience), REQ-5 (non-Latin names). Building
> Assumption Graph: REQ-1 alone fans out to 3 independent layers
> (frontend, backend, database) all encoding "every applicant has a
> surname."
>
> Human Compatibility Score: **40/100 - Needs Attention**.
> Replaying persona "Noor" (single legal name, no permanent address,
> +92 phone number)... **FAILED** - rejected on `last_name`, `address`.

**Operator:** Generate and apply the repair plan.

**Bob (repair):**
```
Patched demo_target/backend/schemas.py:
    nullable last_name/address, E.164 phone, Unicode name support
Patched demo_target/database/migration.sql:
    last_name/address are now nullable columns
Patched demo_target/backend/main.py:
    idempotency-key based dedupe on submission
Patched demo_target/frontend/index.html:
    optional surname/address, international phone, Unicode names accepted
Patched demo_target/frontend/ApplicationForm.tsx:
    optional surname/address, international phone accepted
Patched demo_target/tests/test_applications.py:
    added 5 regression tests for REQ-1..REQ-5
```

**Bob (verify):**
> Running `pytest demo_target/tests -q`... **9 passed** (4 original + 5
> new regression tests). Re-analyzing repository from scratch (no cached
> findings)... 0 findings remaining. Replaying "Noor"...
> **JOURNEY COMPLETED** (application id returned).
>
> Human Compatibility Score: **100/100 - Human-Compatible** (+60 from
> before).

---

This is the exact sequence `python -m analyzer.cli demo` runs (see
`analyzer/cli.py::cmd_demo`), and the exact sequence the dashboard's
Analyze -> Generate Repair Plan -> Apply Demo Fix -> Verify Repair buttons
trigger against the live API.

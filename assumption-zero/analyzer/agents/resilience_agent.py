"""
Resilience Agent

Unlike the other agents (which do static analysis), this agent actually
EXECUTES the demo application in-process using FastAPI's TestClient and
simulates a client retrying a submission after a network interruption
(no response received, so it resends the identical payload). It then
inspects the real database to see whether a duplicate row was created.
This is executable proof, not a heuristic guess.
"""
from __future__ import annotations

from pathlib import Path

from analyzer.models import AgentReport, Finding


def run(demo_target_root: str | Path) -> AgentReport:
    import sys

    repo_root = Path(demo_target_root).parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from demo_target.backend import database
    from demo_target.backend.main import app
    from fastapi.testclient import TestClient

    database.reset_db()
    client = TestClient(app)

    payload = {
        "first_name": "Resilience",
        "last_name": "Probe",
        "address": "1 Test Way",
        "phone": "(555) 000-1111",
    }
    # A well-behaved retrying client generates one idempotency key up front
    # and resends it unchanged on every retry of the SAME submission
    # attempt. This is the standard, correct way to make a retry safe --
    # so this is a fair test of whether the server actually honors it.
    headers = {"Idempotency-Key": "resilience-probe-key-001"}

    # First attempt: server processes it, but we simulate the response
    # never reaching the client (e.g. connection dropped mid-flight).
    first = client.post("/applications", json=payload, headers=headers)

    # The client, having received no confirmation, retries with the exact
    # same payload and the same idempotency key.
    second = client.post("/applications", json=payload, headers=headers)

    rows = client.get("/applications").json()
    matching = [
        r for r in rows
        if r["first_name"] == payload["first_name"] and r["last_name"] == payload["last_name"]
    ]

    findings: list[Finding] = []
    if first.status_code == 201 and second.status_code == 201 and len(matching) >= 2:
        findings.append(
            Finding(
                assumption_id="resilience-duplicate-submission",
                human_requirement="REQ-4",
                layer="resilience",
                file="demo_target/backend/main.py",
                line_or_symbol="create_application()",
                detected_assumption=(
                    "The submission endpoint assumes every request completes "
                    "exactly once and has no idempotency key or dedupe logic."
                ),
                why_it_conflicts=(
                    "POLICY.md REQ-4 requires the system to avoid creating "
                    "duplicate assistance requests when a client retries "
                    "after a dropped connection. Executing two identical "
                    "submissions produced "
                    f"{len(matching)} rows for the same applicant "
                    "instead of one, proving the assumption is violated."
                ),
                severity="high",
                confidence=1.0,
                recommended_fix=(
                    "Accept a client-generated `idempotency_key` header, "
                    "store it on the row, and return the existing row "
                    "instead of inserting a new one on a repeated key."
                ),
            )
        )

    return AgentReport(
        agent="Resilience Agent",
        layer="resilience",
        scanned_summary=(
            "Simulated a dropped-connection retry by submitting an identical "
            "payload twice against a live TestClient instance"
        ),
        findings=findings,
    )

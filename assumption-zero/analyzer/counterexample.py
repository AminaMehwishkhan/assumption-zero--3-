"""
Counterexample Generator & Human Journey Executor

Generates the smallest realistic human scenario that should be accepted
under POLICY.md, then REPLAYS it against the real, running demo
application (via FastAPI's TestClient, i.e. actual request/response
handling, actual Pydantic validation, actual SQLite writes) and records
exactly what fails and why. Nothing here is asserted without executing
real code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


PERSONAS = {
    "noor": {
        "display_name": "Noor",
        "characteristics": [
            "One legal name only (no surname)",
            "No permanent residential address",
            "Pakistani / international phone number",
            "May temporarily lose internet connectivity",
        ],
        "payload": {
            "first_name": "Noor",
            "last_name": None,
            "address": None,
            "phone": "+923001234567",
        },
    }
}


@dataclass
class StepResult:
    step: str
    human_requirement: str
    passed: bool
    detail: str


@dataclass
class JourneyResult:
    persona: str
    display_name: str
    characteristics: list[str]
    passed: bool
    steps: list[StepResult] = field(default_factory=list)
    submitted_id: int | None = None

    def to_dict(self) -> dict:
        return {
            "persona": self.persona,
            "display_name": self.display_name,
            "characteristics": self.characteristics,
            "passed": self.passed,
            "submitted_id": self.submitted_id,
            "steps": [s.__dict__ for s in self.steps],
        }


def _fresh_client():
    """Import lazily so this module has no hard dependency on the demo app
    unless a journey is actually run."""
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from demo_target.backend.main import app
    from fastapi.testclient import TestClient

    return TestClient(app)


def run_journey(persona_key: str = "noor") -> JourneyResult:
    persona = PERSONAS[persona_key]
    payload: dict[str, Any] = dict(persona["payload"])

    result = JourneyResult(
        persona=persona_key,
        display_name=persona["display_name"],
        characteristics=persona["characteristics"],
        passed=False,
    )

    client = _fresh_client()
    res = client.post("/applications", json=payload)

    if res.status_code == 201:
        body = res.json()
        result.submitted_id = body["id"]
        result.passed = True
        result.steps.append(
            StepResult(
                step="Submit application",
                human_requirement="REQ-1,REQ-2,REQ-3",
                passed=True,
                detail=f"Application accepted with id {body['id']}.",
            )
        )
        return result

    # Submission failed -- inspect the real 422 body from Pydantic to
    # attribute each failure to the exact requirement it violates.
    try:
        errors = res.json().get("detail", [])
    except Exception:
        errors = []

    failed_fields = {e.get("loc", [None, None])[-1] for e in errors if isinstance(e, dict)}

    field_to_requirement = {
        "last_name": ("REQ-1", "Applicant has no surname (single legal name)."),
        "address": ("REQ-2", "Applicant has no permanent residential address."),
        "phone": ("REQ-3", "Applicant used an international (+92) phone number."),
    }

    if not failed_fields and res.status_code != 201:
        # Fallback: request rejected but body shape unexpected.
        result.steps.append(
            StepResult(
                step="Submit application",
                human_requirement="REQ-1,REQ-2,REQ-3",
                passed=False,
                detail=f"Request rejected with status {res.status_code}: {res.text}",
            )
        )

    for field_name, (req_id, human_reason) in field_to_requirement.items():
        if field_name in failed_fields:
            result.steps.append(
                StepResult(
                    step=f"Validate `{field_name}`",
                    human_requirement=req_id,
                    passed=False,
                    detail=(
                        f"Server rejected the request because `{field_name}` "
                        f"failed validation. {human_reason} "
                        f"POLICY.md {req_id} says this must be supported."
                    ),
                )
            )
        else:
            result.steps.append(
                StepResult(
                    step=f"Validate `{field_name}`",
                    human_requirement=req_id,
                    passed=True,
                    detail=f"`{field_name}` passed validation.",
                )
            )

    result.passed = all(s.passed for s in result.steps)
    return result

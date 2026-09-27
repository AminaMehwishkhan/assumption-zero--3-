"""
Backend / API Agent

Uses Python's `ast` module to inspect the real Pydantic model in
demo_target/backend/schemas.py: which fields are non-Optional (therefore
required), and whether any validator enforces a narrow, non-international
phone pattern. This is genuine static analysis over the actual source file.
"""
from __future__ import annotations

import ast
from pathlib import Path

from analyzer.models import AgentReport, Finding

REQUIREMENT_BY_FIELD = {
    "last_name": ("REQ-1", "surname"),
    "address": ("REQ-2", "permanent address"),
}


def _is_optional_annotation(annotation: ast.expr) -> bool:
    """Return True if the annotation is Optional[...] / X | None."""
    if isinstance(annotation, ast.Subscript):
        value = annotation.value
        name = getattr(value, "id", None) or getattr(value, "attr", None)
        if name == "Optional":
            return True
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        return True
    return False


def _scan_schema_file(path: Path) -> tuple[list[Finding], list[str]]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    findings: list[Finding] = []
    scanned_models: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        # Only look at classes that subclass BaseModel (real Pydantic models).
        base_names = [getattr(b, "id", getattr(b, "attr", "")) for b in node.bases]
        if "BaseModel" not in base_names:
            continue
        scanned_models.append(node.name)

        # Only input/request models encode a *requirement* on applicants;
        # response/output models (e.g. ApplicationOut) just describe what
        # is already stored, so we don't double-count them as assumptions.
        if "Create" not in node.name and "Request" not in node.name and "In" not in node.name:
            continue

        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                field_name = stmt.target.id
                if field_name in REQUIREMENT_BY_FIELD and not _is_optional_annotation(stmt.annotation):
                    req_id, human_label = REQUIREMENT_BY_FIELD[field_name]
                    findings.append(
                        Finding(
                            assumption_id=f"backend-{field_name}-required",
                            human_requirement=req_id,
                            layer="backend",
                            file=str(path),
                            line_or_symbol=f"{node.name}.{field_name} (line {stmt.lineno})",
                            detected_assumption=(
                                f"Pydantic field `{field_name}` on `{node.name}` is "
                                f"declared as a required non-Optional `str`."
                            ),
                            why_it_conflicts=(
                                f"POLICY.md {req_id} requires applicants without a "
                                f"{human_label} to be supported, but the API schema "
                                f"rejects any request where `{field_name}` is missing "
                                f"or null."
                            ),
                            severity="critical" if field_name == "last_name" else "high",
                            confidence=0.97,
                            recommended_fix=(
                                f"Change `{field_name}: str` to "
                                f"`{field_name}: Optional[str] = None` and remove any "
                                f"validator that rejects an empty value."
                            ),
                        )
                    )

        # Field-level validators that enforce a narrow phone pattern or a
        # Latin-only name pattern.
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                src = ast.get_source_segment(text, stmt) or ""
                if "phone" in stmt.name and ("US_PHONE_PATTERN" in src or "us_pattern" in src.lower()):
                    findings.append(
                        Finding(
                            assumption_id="backend-phone-us-only",
                            human_requirement="REQ-3",
                            layer="backend",
                            file=str(path),
                            line_or_symbol=f"{node.name}.{stmt.name} (line {stmt.lineno})",
                            detected_assumption=(
                                "Server-side validator enforces a US-only NANP "
                                "phone pattern via `US_PHONE_PATTERN`."
                            ),
                            why_it_conflicts=(
                                "POLICY.md REQ-3 requires acceptance of "
                                "international phone numbers (e.g. Pakistani "
                                "+92 numbers), but this validator raises a "
                                "ValueError for any non-US format, even if the "
                                "frontend were fixed."
                            ),
                            severity="high",
                            confidence=0.95,
                            recommended_fix=(
                                "Replace the US-only regex with E.164 "
                                "validation (`^\\+?[1-9]\\d{7,14}$` or a "
                                "phonenumbers library check)."
                            ),
                        )
                    )
                if "latin" in stmt.name.lower() and "LATIN_NAME_PATTERN" in src:
                    findings.append(
                        Finding(
                            assumption_id="backend-name-latin-only",
                            human_requirement="REQ-5",
                            layer="backend",
                            file=str(path),
                            line_or_symbol=f"{node.name}.{stmt.name} (line {stmt.lineno})",
                            detected_assumption=(
                                "Server-side validator rejects any applicant "
                                "name containing non-Latin (e.g. Urdu, Arabic) "
                                "characters via `LATIN_NAME_PATTERN`."
                            ),
                            why_it_conflicts=(
                                "POLICY.md REQ-5 says applicant names in "
                                "non-Latin scripts should be preserved "
                                "correctly, not rejected, but this validator "
                                "raises a ValueError for any such name."
                            ),
                            severity="medium",
                            confidence=0.93,
                            recommended_fix=(
                                "Remove the Latin-only regex; accept any "
                                "non-empty Unicode string for name fields."
                            ),
                        )
                    )

    return findings, scanned_models


def run(demo_target_root: str | Path) -> AgentReport:
    root = Path(demo_target_root) / "backend"
    endpoints_scanned = 0
    findings: list[Finding] = []
    models_scanned: list[str] = []

    schema_file = root / "schemas.py"
    if schema_file.exists():
        f, models = _scan_schema_file(schema_file)
        findings.extend(f)
        models_scanned.extend(models)

    main_file = root / "main.py"
    if main_file.exists():
        text = main_file.read_text(encoding="utf-8")
        endpoints_scanned = len(
            [1 for line in text.splitlines() if line.strip().startswith("@app.")]
        )

    return AgentReport(
        agent="Backend/API Agent",
        layer="backend",
        scanned_summary=(
            f"Scanned {endpoints_scanned} endpoint(s) and "
            f"{len(models_scanned)} schema model(s) in demo_target/backend"
        ),
        findings=findings,
    )

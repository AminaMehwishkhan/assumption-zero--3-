"""
Database Agent

Parses the real migration.sql for demo_target and flags NOT NULL columns
that correspond to a human requirement claiming that field is optional.
"""
from __future__ import annotations

import re
from pathlib import Path

from analyzer.models import AgentReport, Finding

COLUMN_RE = re.compile(
    r'^\s*(?P<name>\w+)\s+(?P<type>\w+)\s+NOT\s+NULL', re.IGNORECASE | re.MULTILINE
)

REQUIREMENT_BY_COLUMN = {
    "last_name": ("REQ-1", "surname"),
    "address": ("REQ-2", "permanent address"),
}


def run(demo_target_root: str | Path) -> AgentReport:
    root = Path(demo_target_root) / "database"
    schema_file = root / "migration.sql"
    findings: list[Finding] = []
    columns_scanned = 0

    if schema_file.exists():
        text = schema_file.read_text(encoding="utf-8")
        for m in COLUMN_RE.finditer(text):
            columns_scanned += 1
            col = m.group("name")
            if col in REQUIREMENT_BY_COLUMN:
                req_id, human_label = REQUIREMENT_BY_COLUMN[col]
                line_no = text[: m.start()].count("\n") + 1
                findings.append(
                    Finding(
                        assumption_id=f"database-{col}-not-null",
                        human_requirement=req_id,
                        layer="database",
                        file=str(schema_file),
                        line_or_symbol=f"applications.{col} (line {line_no})",
                        detected_assumption=(
                            f"Column `{col}` is declared `NOT NULL` in the "
                            f"`applications` table schema."
                        ),
                        why_it_conflicts=(
                            f"POLICY.md {req_id} requires applicants without a "
                            f"{human_label} to be supported end-to-end, but the "
                            f"database will reject an insert with a null "
                            f"`{col}`, even if frontend and backend validation "
                            f"were both fixed."
                        ),
                        severity="critical" if col == "last_name" else "high",
                        confidence=0.98,
                        recommended_fix=(
                            f"Write a migration making `{col}` nullable "
                            f"(`ALTER TABLE applications ALTER COLUMN {col} "
                            f"DROP NOT NULL` / recreate table for SQLite)."
                        ),
                    )
                )

    return AgentReport(
        agent="Database Agent",
        layer="database",
        scanned_summary=f"Scanned schema with {columns_scanned} NOT NULL constraint(s) in migration.sql",
        findings=findings,
    )

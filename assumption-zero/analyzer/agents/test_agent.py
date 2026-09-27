"""
Test Agent

Uses `ast` to enumerate every test function in demo_target/tests, then
checks whether the human requirements from POLICY.md are actually
exercised by any test. Reports a coverage-gap Finding for each
requirement with zero matching tests — real analysis of real test source,
not an assumed gap list.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from analyzer.models import AgentReport, Finding

# Signal substrings that would indicate a test covers the given requirement,
# looked for in test function names, docstrings and source bodies.
COVERAGE_SIGNALS = {
    "REQ-1": [r"no.?surname", r"missing.?last.?name", r"mononym", r"single.?name",
              r'"last_name"\s*:\s*null', r"last_name.*none", r"without.*surname"],
    "REQ-2": [r"no.?address", r"missing.?address", r"without.*address"],
    "REQ-3": [r"international", r"\+92", r"pakistan"],
    "REQ-4": [r"duplicate", r"idempot", r"retr(y|ied|ies)", r"network", r"dropped.?connection"],
    "REQ-5": [r"unicode", r"urdu", r"arabic", r"non.?latin", r"non.?ascii"],
}

FRIENDLY_NAME = {
    "REQ-1": "an applicant without a surname",
    "REQ-2": "an applicant without a permanent address",
    "REQ-3": "an applicant with an international phone number",
    "REQ-4": "a dropped connection / retried submission",
    "REQ-5": "an applicant with a non-Latin-script name",
}


def run(demo_target_root: str | Path) -> AgentReport:
    root = Path(demo_target_root) / "tests"
    test_files = sorted(root.glob("test_*.py"))

    # Only the source of actual `def test_*` functions counts as "coverage" -
    # a comment describing a known gap must not accidentally satisfy the
    # very signal it's describing.
    all_source = ""
    total_tests = 0
    for f in test_files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(text, filename=str(f))
        except SyntaxError:
            continue
        test_fns = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
        ]
        total_tests += len(test_fns)
        for fn in test_fns:
            segment = ast.get_source_segment(text, fn) or ""
            all_source += "\n" + fn.name + "\n" + segment

    findings: list[Finding] = []
    for req_id, patterns in COVERAGE_SIGNALS.items():
        covered = any(re.search(p, all_source, re.IGNORECASE) for p in patterns)
        if not covered:
            file_ref = str(test_files[0]) if test_files else "demo_target/tests/test_applications.py"
            findings.append(
                Finding(
                    assumption_id=f"tests-missing-{req_id.lower()}",
                    human_requirement=req_id,
                    layer="tests",
                    file=file_ref,
                    line_or_symbol="test suite (no matching test function)",
                    detected_assumption=(
                        f"No regression test exercises {FRIENDLY_NAME[req_id]}."
                    ),
                    why_it_conflicts=(
                        f"POLICY.md {req_id} is a binding requirement, but "
                        f"the test suite has zero coverage for it, so a "
                        f"regression could silently reintroduce this "
                        f"contradiction after a fix."
                    ),
                    severity="medium",
                    confidence=0.85,
                    recommended_fix=(
                        f"Add a regression test that submits {FRIENDLY_NAME[req_id]} "
                        f"and asserts a 2xx response."
                    ),
                )
            )

    return AgentReport(
        agent="Test Agent",
        layer="tests",
        scanned_summary=f"Inspected {total_tests} test(s) across {len(test_files)} file(s) in demo_target/tests",
        findings=findings,
    )

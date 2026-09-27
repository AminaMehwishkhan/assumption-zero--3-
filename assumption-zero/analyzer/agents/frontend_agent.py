"""
Frontend Agent

Scans the actual frontend source files under demo_target/frontend for
DOM/JS-level assumptions: required fields and validation patterns that
contradict POLICY.md. This is real static analysis over real files (regex
over JSX/HTML/JS source), not a hardcoded list of "expected bugs".
"""
from __future__ import annotations

import re
from pathlib import Path

from analyzer.models import AgentReport, Finding

REQUIRED_FIELD_RE = re.compile(
    r'(?:required\b|\.required\s*=\s*true)', re.IGNORECASE
)
LAST_NAME_FIELD_RE = re.compile(
    r'(id=["\']last_name["\']|lastName|last name)', re.IGNORECASE
)
ADDRESS_FIELD_RE = re.compile(
    r'(id=["\']address["\']|street address)', re.IGNORECASE
)
# Matches the actual US-only NANP regex *pattern shape* (three-three-four
# digit groups), not just a variable name, so a rename-only "fix" that
# keeps the same broken pattern is still caught, and a real content fix
# (e.g. an E.164 pattern) is correctly recognized as repaired.
US_PHONE_REGEX_RE = re.compile(r'\\d\{3\}\)?[^)]*\\d\{3\}[^)]*\\d\{4\}')

# Matches a Latin-letters-only name validation pattern (e.g.
# /^[A-Za-z\s\-'.]+$/), which rejects non-Latin scripts (Urdu, Arabic, etc).
LATIN_NAME_MESSAGE_RE = re.compile(r"latin letters only", re.IGNORECASE)


LABEL_BLOCK_RE = re.compile(r"<label[^>]*>(.*?)</label>", re.IGNORECASE | re.DOTALL)


def _scan_file(path: Path, findings: list[Finding]) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = str(path)

    # Look at each <label>...</label> block on its own so a `required`
    # input attribute is only attributed to the field that label actually
    # describes, instead of leaking across unrelated parts of the file.
    lastname_required = False
    address_required = False
    for label_block in LABEL_BLOCK_RE.findall(text):
        is_required = bool(REQUIRED_FIELD_RE.search(label_block))
        if not is_required:
            continue
        if LAST_NAME_FIELD_RE.search(label_block):
            lastname_required = True
        if ADDRESS_FIELD_RE.search(label_block):
            address_required = True

    # Also catch the imperative "Last name is required." validation message
    if re.search(r'last name is required', text, re.IGNORECASE):
        lastname_required = True
    if re.search(r'(street )?address is required', text, re.IGNORECASE):
        address_required = True

    if lastname_required:
        line = _find_line(text, "last name")
        findings.append(
            Finding(
                assumption_id="frontend-surname-required",
                human_requirement="REQ-1",
                layer="frontend",
                file=rel,
                line_or_symbol=f"line {line}" if line else "lastName field",
                detected_assumption=(
                    "The applicant's last name / surname is marked as a "
                    "required form field."
                ),
                why_it_conflicts=(
                    "POLICY.md REQ-1 requires the system to support "
                    "applicants with a single legal name (no surname), but "
                    "the form will not let them submit without one."
                ),
                severity="critical",
                confidence=0.95,
                recommended_fix=(
                    "Remove `required` from the last-name input and drop "
                    "the 'Last name is required.' client-side validation "
                    "branch; make last name optional in the submitted payload."
                ),
            )
        )

    if address_required:
        line = _find_line(text, "address")
        findings.append(
            Finding(
                assumption_id="frontend-address-required",
                human_requirement="REQ-2",
                layer="frontend",
                file=rel,
                line_or_symbol=f"line {line}" if line else "address field",
                detected_assumption=(
                    "The applicant's street address is marked as a "
                    "required form field."
                ),
                why_it_conflicts=(
                    "POLICY.md REQ-2 requires support for applicants with "
                    "no permanent residential address, but the form blocks "
                    "submission without a street address."
                ),
                severity="high",
                confidence=0.9,
                recommended_fix=(
                    "Remove `required` from the address input; allow a "
                    "free-text 'current location description' as a fallback."
                ),
            )
        )

    if US_PHONE_REGEX_RE.search(text):
        line = _find_line(text, "US_PHONE_REGEX") or _find_line(text, "\\d{3}")
        findings.append(
            Finding(
                assumption_id="frontend-phone-us-only",
                human_requirement="REQ-3",
                layer="frontend",
                file=rel,
                line_or_symbol=f"line {line}" if line else "phone validation",
                detected_assumption=(
                    "Client-side phone validation only accepts a US-style "
                    "NANP pattern (e.g. (555) 123-4567)."
                ),
                why_it_conflicts=(
                    "POLICY.md REQ-3 requires support for international "
                    "phone numbers, including Pakistani (+92) numbers, but "
                    "the regex rejects any non-US format before the request "
                    "is even sent."
                ),
                severity="high",
                confidence=0.9,
                recommended_fix=(
                    "Replace the US-only regex with E.164 validation "
                    "(e.g. libphonenumber-js) that accepts international "
                    "numbers."
                ),
            )
        )


    if LATIN_NAME_MESSAGE_RE.search(text):
        line = _find_line(text, "latin letters only")
        findings.append(
            Finding(
                assumption_id="frontend-name-latin-only",
                human_requirement="REQ-5",
                layer="frontend",
                file=rel,
                line_or_symbol=f"line {line}" if line else "name validation",
                detected_assumption=(
                    "Client-side validation rejects applicant names "
                    "containing non-Latin (e.g. Urdu, Arabic) characters."
                ),
                why_it_conflicts=(
                    "POLICY.md REQ-5 says names in non-Latin scripts should "
                    "be preserved correctly, but this validation blocks "
                    "submission before the request is even sent."
                ),
                severity="medium",
                confidence=0.9,
                recommended_fix=(
                    "Remove the Latin-only name check; accept any non-empty "
                    "Unicode string for name fields."
                ),
            )
        )


def _find_line(text: str, needle: str) -> int | None:
    for i, line in enumerate(text.splitlines(), start=1):
        if needle.lower() in line.lower():
            return i
    return None


def run(demo_target_root: str | Path) -> AgentReport:
    root = Path(demo_target_root) / "frontend"
    files = sorted(list(root.glob("*.tsx")) + list(root.glob("*.html")) + list(root.glob("*.jsx")))

    findings: list[Finding] = []
    for f in files:
        _scan_file(f, findings)

    # De-duplicate identical assumption_ids found in multiple files, keeping
    # the first (still records which files were scanned in the summary).
    seen = set()
    unique_findings = []
    for f in findings:
        if f.assumption_id in seen:
            continue
        seen.add(f.assumption_id)
        unique_findings.append(f)

    return AgentReport(
        agent="Frontend Agent",
        layer="frontend",
        scanned_summary=f"Scanned {len(files)} frontend source file(s) in demo_target/frontend",
        findings=unique_findings,
    )

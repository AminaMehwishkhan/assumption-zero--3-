"""
Human Compatibility Score

An explainable 0-100 score, NOT an arbitrary number. It starts at 100 and
subtracts severity-weighted penalties for each unresolved assumption, plus
an extra penalty if the hero human journey (Noor) fails outright. Every
point lost/gained is attributable to a specific finding or journey step,
and `diff_scores` produces the "why did the score change" breakdown shown
in the dashboard.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from analyzer.counterexample import JourneyResult
from analyzer.models import Finding

SEVERITY_PENALTY = {
    "critical": 6,
    "high": 4,
    "medium": 2,
    "low": 1,
}

JOURNEY_FAILURE_PENALTY = 8
REQUIREMENT_TOTAL = 5  # REQ-1..REQ-5 tracked in POLICY.md


REQUIREMENT_FRIENDLY = {
    "REQ-1": "surname",
    "REQ-2": "permanent-address",
    "REQ-3": "international-phone",
    "REQ-4": "offline-resilience",
    "REQ-5": "unicode-name",
}


@dataclass
class ScoreLineItem:
    label: str
    points: int  # negative = penalty, positive = bonus


@dataclass
class ScoreResult:
    score: int
    status: str
    requirements_verified: int
    requirements_total: int
    line_items: list[ScoreLineItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "status": self.status,
            "requirements_verified": self.requirements_verified,
            "requirements_total": self.requirements_total,
            "line_items": [li.__dict__ for li in self.line_items],
        }


def _status_for(score: int) -> str:
    if score >= 90:
        return "Human-Compatible"
    if score >= 70:
        return "Minor Gaps"
    return "Needs Attention"


def compute_score(findings: list[Finding], journey: JourneyResult | None = None) -> ScoreResult:
    score = 100
    line_items: list[ScoreLineItem] = []

    for f in findings:
        penalty = SEVERITY_PENALTY.get(f.severity, 3)
        score -= penalty
        line_items.append(
            ScoreLineItem(
                label=f"{f.detected_assumption[:60]} ({f.layer}, {f.severity})",
                points=-penalty,
            )
        )

    if journey is not None and not journey.passed:
        score -= JOURNEY_FAILURE_PENALTY
        line_items.append(
            ScoreLineItem(
                label=f"Human journey '{journey.display_name}' failed end-to-end",
                points=-JOURNEY_FAILURE_PENALTY,
            )
        )

    score = max(0, min(100, score))

    reqs_with_findings = {f.human_requirement for f in findings}
    requirements_verified = REQUIREMENT_TOTAL - len(
        {r for r in reqs_with_findings if r in REQUIREMENT_FRIENDLY}
    )
    requirements_verified = max(0, requirements_verified)

    return ScoreResult(
        score=score,
        status=_status_for(score),
        requirements_verified=requirements_verified,
        requirements_total=REQUIREMENT_TOTAL,
        line_items=line_items,
    )


def diff_scores(before: ScoreResult, after: ScoreResult) -> list[ScoreLineItem]:
    """Human-readable summary of *why* the score improved (or regressed)."""
    before_ids = {li.label for li in before.line_items}
    resolved = [li for li in before.line_items if li.label not in {a.label for a in after.line_items}]

    diff: list[ScoreLineItem] = []
    for li in resolved:
        diff.append(ScoreLineItem(label=f"Resolved: {li.label}", points=abs(li.points)))

    net = after.score - before.score
    diff.append(ScoreLineItem(label="Net Human Compatibility change", points=net))
    return diff

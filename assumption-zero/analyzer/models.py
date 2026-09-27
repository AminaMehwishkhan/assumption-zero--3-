from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal

Layer = Literal["frontend", "backend", "database", "tests", "resilience"]
Severity = Literal["low", "medium", "high", "critical"]

# Repo root — used to make file paths relative for portability and cleaner display
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _normalize_path(p: str) -> str:
    """Convert an absolute path to a path relative to the repo root.
    Keeps the path as-is if it's already relative or can't be relativized."""
    try:
        return str(Path(p).resolve().relative_to(_REPO_ROOT)).replace("\\", "/")
    except (ValueError, OSError):
        return p.replace("\\", "/")


@dataclass
class Finding:
    """Structured output every agent must produce. Matches the schema
    specified in the Assumption Zero design doc exactly."""

    assumption_id: str
    human_requirement: str          # requirement id, e.g. "REQ-1"
    layer: Layer
    file: str                       # real, relative repo path
    line_or_symbol: str             # e.g. "42" or "ApplicationForm.tsx:lastName"
    detected_assumption: str
    why_it_conflicts: str
    severity: Severity
    confidence: float
    recommended_fix: str
    source_excerpt: str | None = None
    affected_journey: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["file"] = _normalize_path(d["file"])
        return d


@dataclass
class AgentReport:
    agent: str
    layer: Layer
    scanned_summary: str             # e.g. "Scanned 3 components..."
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "layer": self.layer,
            "scanned_summary": self.scanned_summary,
            "findings": [f.to_dict() for f in self.findings],
        }

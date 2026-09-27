"""
Repository Analyzer / Orchestrator

Runs the five specialized agents concurrently (real threads, real I/O -
each agent independently reads real files or executes real code), then
merges their findings into an Assumption Graph and computes the Human
Compatibility Score. This module is what both the CLI and the FastAPI
`/api` layer call.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from analyzer import requirements as requirements_mod
from analyzer.agents import (
    backend_agent,
    database_agent,
    frontend_agent,
    resilience_agent,
    test_agent,
)
from analyzer.assumption_graph import build_graph
from analyzer.counterexample import run_journey
from analyzer.models import AgentReport, Finding
from analyzer.scoring import compute_score


def _extract_line_number(value: str | None) -> int | None:
    if not value:
        return None
    match = __import__("re").search(r"(\d+)", value)
    return int(match.group(1)) if match else None


def _attach_source_context(findings: list[Finding], root: Path) -> None:
    for finding in findings:
        if not finding.file:
            continue
        source_path = (root / finding.file).resolve()
        if not source_path.exists():
            continue
        lines = source_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        line_no = _extract_line_number(finding.line_or_symbol)
        if line_no is None:
            finding.source_excerpt = "\n".join(lines[:6])
        else:
            start = max(1, line_no - 2)
            end = min(len(lines), line_no + 2)
            finding.source_excerpt = "\n".join(f"{i}: {lines[i - 1]}" for i in range(start, end + 1))

        if finding.human_requirement == "REQ-1":
            finding.affected_journey = "Noor → Validate last_name → Failed"
        elif finding.human_requirement == "REQ-2":
            finding.affected_journey = "Noor → Validate address → Failed"
        elif finding.human_requirement == "REQ-3":
            finding.affected_journey = "Noor → Validate phone → Failed"
        elif finding.human_requirement == "REQ-4":
            finding.affected_journey = "Noor → Retry submission → Duplicate risk"
        elif finding.human_requirement == "REQ-5":
            finding.affected_journey = "Noor → Validate first_name → Failed"
        else:
            finding.affected_journey = "Noor → Human requirement check → Failed"

AGENTS = {
    "frontend": frontend_agent.run,
    "backend": backend_agent.run,
    "database": database_agent.run,
    "tests": test_agent.run,
    "resilience": resilience_agent.run,
}


def run_full_analysis(demo_target_root: str | Path) -> dict:
    root = Path(demo_target_root)
    policy_path = root / "POLICY.md"

    reqs = requirements_mod.extract_requirements(policy_path)

    agent_reports: dict[str, AgentReport] = {}
    with ThreadPoolExecutor(max_workers=len(AGENTS)) as pool:
        future_to_name = {
            pool.submit(fn, root): name for name, fn in AGENTS.items()
        }
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            agent_reports[name] = future.result()

    all_findings: list[Finding] = []
    for name in AGENTS:  # stable order for deterministic UI
        all_findings.extend(agent_reports[name].findings)

    _attach_source_context(all_findings, root)
    graph = build_graph(all_findings)

    journey = run_journey("noor")

    score = compute_score(all_findings, journey)

    return {
        "requirements": [r.to_dict() for r in reqs],
        "agent_reports": {name: report.to_dict() for name, report in agent_reports.items()},
        "findings": [f.to_dict() for f in all_findings],
        "graph": graph.to_dict(),
        "journey": journey.to_dict(),
        "score": score.to_dict(),
    }

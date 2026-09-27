"""
Command-line entrypoint for Assumption Zero.

Usage (from repo root):
    python -m analyzer.cli analyze
    python -m analyzer.cli journey
    python -m analyzer.cli repair
    python -m analyzer.cli verify
    python -m analyzer.cli demo        # runs the full before -> repair -> after flow
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_TARGET = REPO_ROOT / "demo_target"


def cmd_analyze():
    from analyzer.orchestrator import run_full_analysis
    result = run_full_analysis(DEMO_TARGET)
    print(json.dumps(result, indent=2))


def cmd_journey():
    from analyzer.counterexample import run_journey
    result = run_journey("noor")
    print(json.dumps(result.to_dict(), indent=2))


def cmd_repair():
    from analyzer.repair import apply_all_fixes
    changes = apply_all_fixes(DEMO_TARGET)
    for c in changes:
        print("✓", c)
    if not changes:
        print("No changes applied (already repaired?).")


def cmd_verify():
    from analyzer.verifier import verify_repair
    result = verify_repair(REPO_ROOT)
    print(json.dumps(result, indent=2, default=str))


def cmd_demo():
    from analyzer.orchestrator import run_full_analysis
    from analyzer.counterexample import run_journey
    from analyzer.repair import apply_all_fixes
    from analyzer.verifier import verify_repair

    print("=" * 70)
    print("BEFORE: analyzing demo_target...")
    before = run_full_analysis(DEMO_TARGET)
    print(f"Human Compatibility Score: {before['score']['score']}/100 ({before['score']['status']})")
    print(f"Findings: {len(before['findings'])}")
    print(f"Noor journey passed: {before['journey']['passed']}")

    print("\n" + "=" * 70)
    print("Applying repair plan...")
    changes = apply_all_fixes(DEMO_TARGET)
    for c in changes:
        print("✓", c)

    print("\n" + "=" * 70)
    print("AFTER: verifying repair...")
    result = verify_repair(REPO_ROOT)
    after = result["analysis_after"]
    print(f"pytest passed: {result['pytest']['passed']}")
    print(f"Human Compatibility Score: {after['score']['score']}/100 ({after['score']['status']})")
    print(f"Findings remaining: {len(after['findings'])}")
    print(f"Noor journey passed: {after['journey']['passed']}")
    print("=" * 70)


COMMANDS = {
    "analyze": cmd_analyze,
    "journey": cmd_journey,
    "repair": cmd_repair,
    "verify": cmd_verify,
    "demo": cmd_demo,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python -m analyzer.cli [{'|'.join(COMMANDS)}]")
        sys.exit(1)
    COMMANDS[sys.argv[1]]()

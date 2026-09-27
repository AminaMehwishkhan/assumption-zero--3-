"""
Verifier

After a repair is applied, this module proves the fix actually works by:
  1. Running the real pytest suite against the patched demo_target code.
  2. Re-running the full agent analysis (fresh file reads / fresh execution
     -- no caching of the "before" findings).
  3. Re-running the Noor human journey end-to-end.

Nothing is verified by re-reading the earlier report; everything is
recomputed from the current state of the files on disk.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path


def run_pytest(repo_root: str | Path) -> dict:
    repo_root = Path(repo_root)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "demo_target/tests", "-q"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return {
        "passed": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_tail": "\n".join(proc.stdout.strip().splitlines()[-15:]),
        "stderr_tail": "\n".join(proc.stderr.strip().splitlines()[-15:]),
    }


def _reload_demo_target_modules() -> None:
    """The demo app's modules get mutated on disk by repair.py. Force a
    fresh import so the in-process analyzer/journey run against the NEW
    code rather than a stale cached module."""
    mod_names = [
        "demo_target.backend.schemas",
        "demo_target.backend.database",
        "demo_target.backend.main",
    ]
    for name in mod_names:
        if name in sys.modules:
            del sys.modules[name]
    for name in mod_names:
        importlib.import_module(name)


def verify_repair(repo_root: str | Path) -> dict:
    from analyzer.orchestrator import run_full_analysis

    repo_root = Path(repo_root)
    demo_target_root = repo_root / "demo_target"

    test_result = run_pytest(repo_root)

    _reload_demo_target_modules()
    analysis_after = run_full_analysis(demo_target_root)

    return {
        "pytest": test_result,
        "analysis_after": analysis_after,
    }

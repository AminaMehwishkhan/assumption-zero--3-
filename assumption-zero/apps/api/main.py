"""
Assumption Zero API

Thin FastAPI layer over the analyzer package. This process also serves the
dashboard itself (web/index.html) as a static site at "/", so running one
server gets you both the API and the UI at http://localhost:8010 — no
separate static file server needed. Every endpoint here calls real
analyzer code — there is no mocked response.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEMO_TARGET = REPO_ROOT / "demo_target"
WEB_DIR = REPO_ROOT / "apps" / "web"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

app = FastAPI(title="Assumption Zero API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/favicon.ico")
def favicon():
    # Avoids noisy 404s in the server log for the browser's automatic
    # favicon request; the dashboard itself sets no favicon.
    return Response(status_code=204)


@app.get("/api/policy")
def get_policy():
    from analyzer.requirements import extract_requirements
    reqs = extract_requirements(DEMO_TARGET / "POLICY.md")
    return {
        "policy_text": (DEMO_TARGET / "POLICY.md").read_text(encoding="utf-8"),
        "requirements": [r.to_dict() for r in reqs],
    }


@app.post("/api/analyze")
def analyze():
    """Runs the full 5-agent parallel analysis + graph + journey + score."""
    from analyzer.orchestrator import run_full_analysis
    start = time.time()
    result = run_full_analysis(DEMO_TARGET)
    result["elapsed_seconds"] = round(time.time() - start, 3)
    return result


@app.get("/api/score-breakdown")
def score_breakdown():
    """Returns a detailed, human-readable breakdown of the current score
    and per-layer finding counts — useful for the dashboard's score card."""
    from analyzer.orchestrator import run_full_analysis
    result = run_full_analysis(DEMO_TARGET)
    score = result["score"]
    findings = result["findings"]
    by_layer = {}
    by_sev = {}
    by_req = {}
    for f in findings:
        by_layer[f["layer"]] = by_layer.get(f["layer"], 0) + 1
        by_sev[f["severity"]] = by_sev.get(f["severity"], 0) + 1
        by_req[f["human_requirement"]] = by_req.get(f["human_requirement"], 0) + 1
    return {
        "score": score,
        "finding_count": len(findings),
        "by_layer": by_layer,
        "by_severity": by_sev,
        "by_requirement": by_req,
    }


@app.post("/api/journey/{persona_key}")
def run_journey(persona_key: str = "noor"):
    from analyzer.counterexample import run_journey as _run_journey
    result = _run_journey(persona_key)
    return result.to_dict()


@app.get("/api/repair-plan")
def repair_plan():
    from analyzer.repair import generate_plan
    plan = generate_plan(DEMO_TARGET)
    return plan.to_dict()


class RepairApplyResponse(BaseModel):
    applied: list[str]


@app.post("/api/repair/apply", response_model=RepairApplyResponse)
def apply_repair():
    """Applies REAL patches to demo_target's source files on disk."""
    from analyzer.repair import apply_all_fixes
    changes = apply_all_fixes(DEMO_TARGET)
    return RepairApplyResponse(applied=changes)


@app.post("/api/verify")
def verify():
    """Re-runs pytest + re-analyzes + re-runs the Noor journey against
    whatever is currently on disk (post-repair or not)."""
    from analyzer.verifier import verify_repair
    return verify_repair(REPO_ROOT)


@app.post("/api/reset-demo")
def reset_demo():
    """Restores demo_target to its original, intentionally-flawed state
    from the reference copy in reports/original_demo_target_snapshot, so
    judges can re-run the whole before->after flow repeatedly."""
    import shutil
    snapshot = REPO_ROOT / "reports" / "original_demo_target_snapshot"
    if not snapshot.exists():
        return {"restored": False, "reason": "no snapshot found"}
    if DEMO_TARGET.exists():
        shutil.rmtree(DEMO_TARGET)
    shutil.copytree(snapshot, DEMO_TARGET)
    db_path = DEMO_TARGET / "backend" / "rapidrelief.db"
    if db_path.exists():
        db_path.unlink()
    return {"restored": True}


# Serve the dashboard itself. Mounted last so it never shadows the /api/*
# and /health routes declared above — Starlette matches those first and
# only falls through to this static mount for anything else, including
# "/" (index.html) and any other file under web/.
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="dashboard")

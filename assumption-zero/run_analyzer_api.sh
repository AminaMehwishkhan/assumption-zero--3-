#!/usr/bin/env bash
# Runs the Assumption Zero analyzer API + dashboard on http://localhost:8010
# The dashboard is served from this same address.
set -e
cd "$(dirname "$0")"
./setup.sh
echo "Starting Assumption Zero analyzer API + dashboard on http://localhost:8010 ..."
echo "Open http://localhost:8010 in your browser once this says 'Application startup complete'."
.venv/bin/python -m uvicorn apps.api.main:app --reload --port 8010

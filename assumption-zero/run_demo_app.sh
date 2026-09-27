#!/usr/bin/env bash
# Runs the flawed demo application (RapidRelief) on http://localhost:8000
set -e
cd "$(dirname "$0")"
./setup.sh
echo "Starting RapidRelief demo app on http://localhost:8000 ..."
.venv/bin/python -m uvicorn demo_target.backend.main:app --reload --port 8000

#!/usr/bin/env bash
# Shared setup: creates .venv and installs dependencies exactly once.
# Called by run_demo_app.sh, run_analyzer_api.sh, and start_all.sh so
# nothing ever installs into the same venv concurrently (which corrupts
# the install if two servers try to start at the same time).
set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    echo "Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

REQ_HASH=$(shasum -a 256 requirements.txt 2>/dev/null | awk '{print $1}' || sha256sum requirements.txt | awk '{print $1}')
MARKER=.venv/.installed

if [ ! -f "$MARKER" ] || [ "$(cat "$MARKER" 2>/dev/null)" != "$REQ_HASH" ]; then
    echo "Installing dependencies (first run, or requirements.txt changed)..."
    .venv/bin/python -m pip install --quiet --upgrade pip
    .venv/bin/python -m pip install --quiet -r requirements.txt
    echo "$REQ_HASH" > "$MARKER"
else
    echo "Dependencies already installed, skipping."
fi

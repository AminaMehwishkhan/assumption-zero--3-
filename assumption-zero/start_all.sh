#!/usr/bin/env bash
# Assumption Zero - one-command macOS/Linux launcher.
# Runs setup ONCE (synchronously, so the two servers never race to
# install into the same venv), then starts both servers in the
# background and opens the dashboard.
set -e
cd "$(dirname "$0")"

./setup.sh

echo "Starting RapidRelief demo app (http://localhost:8000)..."
(.venv/bin/python -m uvicorn demo_target.backend.main:app --port 8000) > /tmp/assumption-zero-demo-app.log 2>&1 &
DEMO_PID=$!

echo "Starting analyzer API + dashboard (http://localhost:8010)..."
(.venv/bin/python -m uvicorn apps.api.main:app --port 8010) > /tmp/assumption-zero-analyzer-api.log 2>&1 &
API_PID=$!

echo "Waiting for servers to start..."
sleep 3

echo "Opening dashboard in your browser..."
if command -v open >/dev/null 2>&1; then
    open http://localhost:8010          # macOS
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:8010      # Linux
else
    echo "Open http://localhost:8010 in your browser."
fi

echo ""
echo "Both servers are running in the background (PIDs: $DEMO_PID, $API_PID)."
echo "Logs: /tmp/assumption-zero-demo-app.log and /tmp/assumption-zero-analyzer-api.log"
echo "Press Ctrl+C to stop this script (servers will keep running)."
echo "To stop the servers: kill $DEMO_PID $API_PID"
wait

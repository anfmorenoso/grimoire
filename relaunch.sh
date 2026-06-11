#!/bin/bash
# Kill processes on backend (8000) and frontend (5173) ports, then restart both.
set -e

GRIMOIRE="$(cd "$(dirname "$0")" && pwd)"

kill_port() {
  local port=$1
  local pids
  pids=$(lsof -ti tcp:"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "Killing process(es) on port $port: $pids"
    echo "$pids" | xargs kill -9
  else
    echo "Port $port is free"
  fi
}

echo "=== Stopping servers ==="
kill_port 8000
kill_port 5173

# Small pause to let sockets release
sleep 0.5

echo ""
echo "=== Starting backend (port 8000) ==="
cd "$GRIMOIRE/backend"
~/.local/bin/uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo ""
echo "=== Starting frontend (port 5173) ==="
cd "$GRIMOIRE/frontend"
npm run dev -- --host &
FRONTEND_PID=$!

echo ""
echo "Backend PID : $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Press Ctrl+C to stop both servers."

# Forward Ctrl+C to both children
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait

#!/bin/bash
set -e

GRIMOIRE="$(cd "$(dirname "$0")" && pwd)"
IMAGE="grimoire-app"
CONTAINER="grimoire-app"

echo "=== Stopping existing servers ==="
docker stop "$CONTAINER" 2>/dev/null && docker rm "$CONTAINER" 2>/dev/null || true
for port in 7860 8000 5173; do
  pids=$(lsof -ti tcp:"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "Killing process(es) on port $port: $pids"
    echo "$pids" | xargs kill -9
  fi
done

echo ""
echo "=== Building image ==="
docker build -t "$IMAGE" "$GRIMOIRE"

echo ""
echo "=== Starting container (port 7860) ==="
docker run -d --name "$CONTAINER" --env-file "$GRIMOIRE/.env" -p 7860:7860 "$IMAGE"

echo ""
echo "URL: http://localhost:7860"
echo ""
echo "Logs (Ctrl+C detaches — container keeps running):"
docker logs -f "$CONTAINER"

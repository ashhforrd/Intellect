#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PID=""
WORKER_PID=""
FRONTEND_PID=""
CLEANED_UP=0

terminate_process_tree() {
  local pid="$1"
  local child

  if command -v pgrep >/dev/null 2>&1; then
    for child in $(pgrep -P "$pid" 2>/dev/null || true); do
      terminate_process_tree "$child"
    done
  fi

  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
  fi
}

cleanup() {
  if [[ "$CLEANED_UP" -eq 1 ]]; then
    return
  fi
  CLEANED_UP=1

  if [[ -z "$API_PID" && -z "$WORKER_PID" && -z "$FRONTEND_PID" ]]; then
    return
  fi

  echo
  echo "Stopping Intellect development services..."

  for pid in "$API_PID" "$WORKER_PID" "$FRONTEND_PID"; do
    if [[ -n "$pid" ]]; then
      terminate_process_tree "$pid"
    fi
  done

  for pid in "$API_PID" "$WORKER_PID" "$FRONTEND_PID"; do
    if [[ -n "$pid" ]]; then
      wait "$pid" 2>/dev/null || true
    fi
  done
}

handle_signal() {
  exit 130
}

trap cleanup EXIT
trap handle_signal INT TERM

for command in docker uv npm; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Required command not found: $command" >&2
    exit 1
  fi
done

if [[ ! -f "$ROOT_DIR/.env" ]]; then
  echo "Missing $ROOT_DIR/.env. Copy .env.example and configure it first." >&2
  exit 1
fi

if [[ ! -d "$ROOT_DIR/frontend/node_modules" ]]; then
  echo "Frontend dependencies are missing. Run: cd frontend && npm install" >&2
  exit 1
fi

if command -v lsof >/dev/null 2>&1; then
  for port in 8000 5173; do
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "Port $port is already in use. Stop the existing service before running this script." >&2
      lsof -nP -iTCP:"$port" -sTCP:LISTEN >&2
      exit 1
    fi
  done
fi

cd "$ROOT_DIR"

export AWS_PROFILE="${AWS_PROFILE:-document-intelligence}"

echo "Starting PostgreSQL..."
docker compose up -d --wait database

echo "Applying database migrations..."
uv run alembic upgrade head

echo "Starting API on http://127.0.0.1:8000..."
uv run uvicorn personal_document_intelligence_api.main:app --reload &
API_PID=$!

echo "Starting document worker with AWS profile '$AWS_PROFILE'..."
uv run python -m personal_document_intelligence_api.workers.runner &
WORKER_PID=$!

echo "Starting frontend on http://localhost:5173..."
(
  cd "$ROOT_DIR/frontend"
  npm run dev
) &
FRONTEND_PID=$!

echo
echo "Intellect is running. Press Ctrl+C to stop the API, worker, and frontend."

while true; do
  for service in "api:$API_PID" "worker:$WORKER_PID" "frontend:$FRONTEND_PID"; do
    name="${service%%:*}"
    pid="${service##*:}"

    if ! kill -0 "$pid" 2>/dev/null; then
      if wait "$pid"; then
        status=0
      else
        status=$?
      fi

      echo "$name stopped unexpectedly (exit code $status)." >&2
      exit "$status"
    fi
  done

  sleep 1
done

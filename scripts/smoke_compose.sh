#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

cleanup() {
  docker compose down -v --remove-orphans >/dev/null 2>&1 || true
}

trap cleanup EXIT

docker compose config >/dev/null
docker compose up -d --build

for attempt in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:8000/health" >/tmp/docustruct-compose-health.json; then
    break
  fi
  sleep 2
done

curl -fsS "http://127.0.0.1:8000/health"
echo
curl -fsS "http://127.0.0.1:8000/metrics"
echo

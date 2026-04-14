#!/usr/bin/env bash
set -euo pipefail
if [[ "${API_RELOAD:-false}" == "true" ]]; then
  uvicorn docustruct_ai.main:app --host 0.0.0.0 --port 8000 --reload
else
  uvicorn docustruct_ai.main:app --host 0.0.0.0 --port 8000
fi

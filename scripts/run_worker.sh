#!/usr/bin/env bash
set -euo pipefail
celery -A docustruct_ai.services.worker.celery_app worker --loglevel=INFO

PYTHON ?= python3

.PHONY: install dev api worker test lint demo-fixtures db-upgrade db-revision

install:
	$(PYTHON) -m pip install -e .[dev]

dev:
	uvicorn docustruct_ai.main:app --host 0.0.0.0 --port 8000 --reload

api:
	uvicorn docustruct_ai.main:app --host 0.0.0.0 --port 8000

worker:
	celery -A docustruct_ai.services.worker.celery_app worker --loglevel=INFO

test:
	pytest -q

demo-fixtures:
	$(PYTHON) scripts/generate_demo_documents.py

db-upgrade:
	alembic upgrade head

db-revision:
	alembic revision --autogenerate -m "$(m)"

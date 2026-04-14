PYTHON ?= python3

.PHONY: install dev api worker test ci lint demo-fixtures db-upgrade db-revision smoke-compose

install:
	$(PYTHON) -m pip install -e .[dev]

dev:
	uvicorn docustruct_ai.main:app --host 0.0.0.0 --port 8000 --reload

api:
	uvicorn docustruct_ai.main:app --host 0.0.0.0 --port 8000

worker:
	celery -A docustruct_ai.services.worker.celery_app worker --loglevel=INFO

smoke-compose:
	./scripts/smoke_compose.sh

test:
	pytest -q

ci:
	python -m compileall src tests scripts
	pytest -q
	DATABASE_URL=sqlite:///./ci.db alembic upgrade head
	python scripts/smoke_pipeline.py
	python scripts/smoke_api_flow.py
	python scripts/smoke_async_flow.py

demo-fixtures:
	$(PYTHON) scripts/generate_demo_documents.py

db-upgrade:
	alembic upgrade head

db-revision:
	alembic revision --autogenerate -m "$(m)"

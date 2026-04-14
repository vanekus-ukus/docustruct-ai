PYTHON ?= python3

.PHONY: install dev api worker test ci lint demo-fixtures db-upgrade db-revision smoke-compose benchmark-smoke

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

benchmark-smoke:
	python scripts/run_benchmark.py --input examples/evaluation/invoice_benchmark.json --name invoice-benchmark-smoke --document-type invoice --database-url sqlite:///./benchmark.db --artifacts-root ./benchmark_artifacts

test:
	pytest -q

ci:
	python -m compileall src tests scripts
	pytest -q
	DATABASE_URL=sqlite:///./ci.db alembic upgrade head
	python scripts/smoke_pipeline.py
	python scripts/smoke_api_flow.py
	python scripts/smoke_async_flow.py
	python scripts/run_benchmark.py --input examples/evaluation/invoice_benchmark.json --name invoice-benchmark-ci --document-type invoice --database-url sqlite:///./benchmark.db --artifacts-root ./benchmark_artifacts

demo-fixtures:
	$(PYTHON) scripts/generate_demo_documents.py

db-upgrade:
	alembic upgrade head

db-revision:
	alembic revision --autogenerate -m "$(m)"

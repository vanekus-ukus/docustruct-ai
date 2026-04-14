# docustruct-ai

Минимальный open-source проект для структурной обработки документов.

Сейчас в проекте уже есть рабочий baseline для:
- `invoice`
- `act`
- `contract`

Дополнительно уже реализовано:
- conditional `VLM fallback` path для сложных документов;
- provider-backed VLM adapter layer с local mock provider;
- offline benchmark CLI с сохранением evaluation artifacts.

## Локальный запуск

```bash
python -m pip install -e .[dev]
cp .env.example .env
alembic upgrade head
uvicorn docustruct_ai.main:app --reload
```

## Docker

```bash
docker compose up --build
```

Для быстрой проверки containerized стека:

```bash
make smoke-compose
```

## Полезное

- API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- Тесты: `./.venv/bin/python -m pytest -q`
- CI smoke: `PATH=./.venv/bin:$PATH make ci`
- Benchmark smoke: `PATH=./.venv/bin:$PATH make benchmark-smoke`
- Compare benchmark smoke: `PATH=./.venv/bin:$PATH make compare-benchmarks-smoke`

## Что сейчас проверено

- извлечение `invoice`, `act`, `contract` из synthetic PDF;
- routing в `accepted` и `needs_review`;
- review flow для шумного invoice;
- сохранение результатов и review decisions;
- queued async path с сохранением `worker_task_id`;
- compose stack с `PostgreSQL + Redis + api + worker`;
- conditional VLM fallback с детерминированным local stub path;
- provider-backed VLM adapter layer для будущих внешних backends;
- benchmark CLI для offline evaluation;
- CLI для сравнения benchmark summary между двумя режимами/движками;
- Alembic migration smoke;
- GitHub Actions для тестов и smoke scripts.

## Smoke scripts

```bash
./.venv/bin/python scripts/smoke_pipeline.py
./.venv/bin/python scripts/smoke_api_flow.py
./.venv/bin/python scripts/smoke_async_flow.py
./.venv/bin/python scripts/run_benchmark.py --input examples/evaluation/invoice_benchmark.json --name invoice-local-benchmark --document-type invoice
```

Первый скрипт проверяет pipeline по fixture-документам.

Второй скрипт проверяет API-layer flow:
- upload
- result
- review submit

Третий скрипт проверяет queued/eager async path:
- upload в async mode
- сохранение `job_id` и `worker_task_id`
- корректный финальный status/result после worker execution

Четвёртая команда запускает offline benchmark:
- читает evaluation items из JSON
- сохраняет summary в JSON и Markdown
- пишет запись `evaluation_runs` в БД

## Структура

- `src/docustruct_ai/` — код приложения
- `docs/` — документация
- `tests/` — тесты
- `examples/` — demo-данные

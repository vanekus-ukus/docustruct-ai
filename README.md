# docustruct-ai

Минимальный open-source проект для структурной обработки документов.

Сейчас в проекте уже есть рабочий baseline для:
- `invoice`
- `act`
- `contract`

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

## Полезное

- API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- Тесты: `./.venv/bin/python -m pytest -q`
- CI smoke: `PATH=./.venv/bin:$PATH make ci`

## Что сейчас проверено

- извлечение `invoice`, `act`, `contract` из synthetic PDF;
- routing в `accepted` и `needs_review`;
- review flow для шумного invoice;
- сохранение результатов и review decisions;
- queued async path с сохранением `worker_task_id`;
- Alembic migration smoke;
- GitHub Actions для тестов и smoke scripts.

## Smoke scripts

```bash
./.venv/bin/python scripts/smoke_pipeline.py
./.venv/bin/python scripts/smoke_api_flow.py
./.venv/bin/python scripts/smoke_async_flow.py
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

## Структура

- `src/docustruct_ai/` — код приложения
- `docs/` — документация
- `tests/` — тесты
- `examples/` — demo-данные

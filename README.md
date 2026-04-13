# docustruct-ai

Минимальный open-source проект для структурной обработки документов.

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

## Структура

- `src/docustruct_ai/` — код приложения
- `docs/` — документация
- `tests/` — тесты
- `examples/` — demo-данные

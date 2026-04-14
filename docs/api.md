# API

## Общие принципы

- API реализован на FastAPI.
- Все response-модели типизированы через Pydantic v2.
- Основной формат обмена: `application/json`.
- Upload endpoint принимает `multipart/form-data`.

## `POST /documents/upload`

Загружает документ, создаёт записи в БД и запускает pipeline.

### Параметры

- `file`: бинарный файл (`PDF`, `PNG`, `JPG`, `JPEG`)
- `document_type`: один из `invoice`, `act`, `contract`
- `external_id`: опциональный внешний идентификатор

### Пример

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@examples/generated/demo_invoice.pdf" \
  -F "document_type=invoice" \
  -F "external_id=invoice-demo-001"
```

### Ответ

```json
{
  "document_id": "8bd841e3-0f32-4272-afdb-b070242e3114",
  "job_id": "4b68c4cf-29b5-48c9-8201-cb953bc39c7f",
  "worker_task_id": "54df42fd-c706-41d5-9236-0641c06253de",
  "status": "queued"
}
```

Если `EXECUTION_MODE=inline`, сервис возвращает тот же контракт, но со статусом `completed` и `worker_task_id = null`.

## `GET /documents/{id}`

Возвращает карточку документа:
- метаданные;
- тип;
- статус;
- routing state;
- confidence.

## `GET /documents/{id}/status`

Возвращает текущий статус job/pipeline и краткую диагностику.

### Основные поля ответа

- `document_id`
- `status`
- `routing_state`
- `job_id`
- `worker_task_id`
- `latest_job_status`
- `error_message`
- `started_at`
- `finished_at`
- `confidence_score`

## `GET /documents/{id}/result`

Возвращает финальный результат:
- schema-compliant payload;
- field-level results;
- evidence;
- validation report;
- routing explanation;
- confidence.

## `GET /documents/{id}/review`

Возвращает минимальный review UI в HTML-формате для спорных полей документа.

Reviewer видит:
- candidate value;
- validation status;
- evidence;
- raw OCR text;
- страницу документа.

## `POST /review/tasks/{id}/submit`

Сохраняет решение reviewer’а.

### Тело запроса

```json
{
  "decision": "edit",
  "final_value": "INV-2024-001",
  "reviewer": "qa@example.com",
  "comment": "Исправлен номер счёта по bbox"
}
```

### Возможные решения

- `accept`
- `edit`
- `unsupported`

## `POST /evaluation/run`

Запускает evaluation по набору предсказаний и эталонных ответов.

### Пример тела

```json
{
  "name": "invoice-baseline-run",
  "document_type": "invoice",
  "items": [
    {
      "document_id": "doc-1",
      "prediction": {"invoice_number": "INV-001"},
      "ground_truth": {"invoice_number": "INV-001"}
    }
  ]
}
```

## `GET /health`

Возвращает состояние сервиса:
- приложение;
- база данных;
- storage root.

## `GET /metrics`

Если включён persistence, endpoint отдаёт агрегированные operational metrics:
- documents total;
- review tasks open;
- accepted documents;
- rejected documents.

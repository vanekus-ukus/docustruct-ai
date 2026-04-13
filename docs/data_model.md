# Модель данных

## Принципы

Реляционная схема строится вокруг документа как первичного объекта и обеспечивает:
- отслеживание полного жизненного цикла обработки;
- audit trail по engine runs;
- field-level provenance;
- review history;
- хранение evaluation-результатов.

## Основные таблицы

### `documents`

Корневой объект документа.

Поля:
- `id`
- `external_id`
- `document_type`
- `filename`
- `mime_type`
- `source_path`
- `status`
- `routing_state`
- `quality_score`
- `confidence_score`
- `metadata_json`
- `created_at`
- `updated_at`

### `pages`

Страницы документа и связанные артефакты.

Поля:
- `id`
- `document_id`
- `page_number`
- `width`
- `height`
- `rotation`
- `image_path`
- `metadata_json`

### `jobs`

Фоновая или inline обработка.

Поля:
- `id`
- `document_id`
- `job_type`
- `status`
- `error_message`
- `started_at`
- `finished_at`

### `engine_runs`

Трассировка вызовов парсеров, OCR, extraction и VLM.

Поля:
- `id`
- `document_id`
- `job_id`
- `engine_type`
- `engine_name`
- `engine_version`
- `status`
- `input_payload`
- `output_payload`
- `metrics_json`
- `created_at`

### `parsed_regions`

Результаты структурного разбора страницы.

Поля:
- `id`
- `document_id`
- `page_id`
- `region_type`
- `bbox_json`
- `text`
- `reading_order`
- `metadata_json`

### `ocr_spans`

Токены/линии OCR.

Поля:
- `id`
- `document_id`
- `page_id`
- `span_type`
- `text`
- `bbox_json`
- `confidence`
- `source_engine`
- `reading_order`
- `metadata_json`

### `extracted_entities`

Логическая сущность извлечения для схемы документа.

Поля:
- `id`
- `document_id`
- `schema_name`
- `schema_version`
- `payload_json`
- `created_at`

### `extracted_fields`

Field-level результат extraction.

Поля:
- `id`
- `entity_id`
- `field_name`
- `value_text`
- `normalized_value`
- `value_type`
- `confidence`
- `routing_state`
- `is_required`
- `metadata_json`

### `field_evidence`

Grounding/evidence по каждому полю.

Поля:
- `id`
- `field_id`
- `page_number`
- `bbox_json`
- `evidence_text`
- `source_engine`
- `source_region_id`
- `grounding_score`

### `validation_reports`

Результаты field-level и document-level validation.

Поля:
- `id`
- `document_id`
- `field_id`
- `scope`
- `status`
- `rule_name`
- `message`
- `details_json`

### `review_tasks`

Задачи на ручную проверку.

Поля:
- `id`
- `document_id`
- `field_id`
- `status`
- `reason`
- `candidate_value`
- `created_at`
- `completed_at`

### `review_decisions`

Решения reviewer’ов.

Поля:
- `id`
- `review_task_id`
- `decision`
- `final_value`
- `reviewer`
- `comment`
- `created_at`

### `evaluation_runs`

История benchmark/evaluation.

Поля:
- `id`
- `name`
- `status`
- `document_type`
- `summary_json`
- `report_path`
- `created_at`

## Связи

- `documents` 1:N `pages`
- `documents` 1:N `jobs`
- `documents` 1:N `engine_runs`
- `documents` 1:N `parsed_regions`
- `documents` 1:N `ocr_spans`
- `documents` 1:N `validation_reports`
- `documents` 1:1..N `extracted_entities`
- `extracted_entities` 1:N `extracted_fields`
- `extracted_fields` 1:N `field_evidence`
- `extracted_fields` 1:N `validation_reports`
- `extracted_fields` 1:0..N `review_tasks`
- `review_tasks` 1:N `review_decisions`

## Почему именно такая модель

- позволяет хранить как финальный результат, так и промежуточные артефакты;
- поддерживает explainability и auditability;
- пригодна для offline evaluation и error analysis;
- легко расширяется под несколько OCR/VLM engines;
- не смешивает schema contracts и persistence concerns.

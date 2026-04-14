# Описание модулей

## `api`

Внешний HTTP-слой на FastAPI. Отвечает за типизированные request/response модели, загрузку документов, статусные endpoints, review UI и evaluation API.

## `core`

Общие доменные типы и внутренние контракты системы:
- `ParsedDocument`
- `ParsedPage`
- `Region`
- `Span`
- `FieldEvidence`
- `DocumentResult`

## `ingestion`

Принимает бинарный документ, сохраняет исходный файл, создаёт записи `document/job`, материализует страницы и готовит артефакты для downstream-пайплайна.

## `parsing`

Преобразует документ в структурное layout-представление. В MVP использует эвристический parser, выделяющий текстовые блоки, KV-кандидаты и table-like регионы.

## `ocr`

Содержит pluggable OCR adapters. Текущая baseline-реализация основана на PyMuPDF text layer для детерминированного локального demo flow.

## `vlm`

Точка расширения под vision-language extraction backends. В текущем состоянии есть:
- `stub` backend;
- provider-backed backend;
- mock provider для локального deterministic flow без внешнего API.

## `extraction`

Schema-first extraction слой:
- registry схем по типам документов;
- document-specific extractors;
- orchestrator, объединяющий parsing, OCR и optional VLM candidate.

## `grounding`

Привязка каждого поля к конкретному evidence в документе: страница, `bbox`, текстовый фрагмент, источник и grounding score.

## `validation`

Field-level и document-level проверки:
- обязательность полей;
- даты;
- суммы;
- cross-field consistency;
- line-item consistency.

## `confidence`

Агрегирует сигналы качества документа, наличия evidence и статуса validation в per-field и document-level confidence.

## `routing`

Explainable routing в `accepted`, `needs_review`, `rejected` на основе confidence и причин, пригодных для аудита.

## `review`

Selective human review: создание review tasks, хранение решений reviewer’ов и минимальный UI для спорных полей.

## `storage`

Абстракция файлового хранилища. В MVP реализован локальный backend, но интерфейс совместим с будущим S3-like хранилищем.

## `evaluation`

Field-aware benchmark-подсистема с поддержкой нескольких scoring modes и сохранением JSON/Markdown summary.

## `db` и `models`

SQLAlchemy ORM, session management, реляционная схема и миграции Alembic.

## `services`

Оркестраторы верхнего уровня:
- `DocumentPipelineService`
- `DocumentQueryService`
- `ReviewService`
- `EvaluationService`
- Celery worker entrypoint

## `utils`

Небольшие нормализаторы и текстовые helper-функции, которые не должны зависеть от инфраструктурных модулей.

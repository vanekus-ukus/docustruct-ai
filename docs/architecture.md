# Архитектура docustruct-ai

## Цели архитектуры

`docustruct-ai` проектируется как модульная платформа для гибридного извлечения структурированных данных из документов. Основная задача MVP — показать production-grade каркас, в котором OCR, parsing, extraction, grounding, validation, confidence и review являются независимыми, заменяемыми подсистемами.

## Логический конвейер

1. `Ingestion`
   Принимает файл, создаёт `document` и `job`, сохраняет исходный артефакт, извлекает базовые метаданные, рендерит страницы для PDF.

2. `Parsing`
   Преобразует страницы в внутреннюю модель `ParsedDocument` и выделяет регионы, зоны текста, таблицы и кандидаты на key-value.

3. `OCR`
   Запускает выбранный OCR backend и приводит результат к унифицированной модели `OCRSpan`.

4. `Extraction`
   Выбирает schema registry по типу документа, объединяет parsing + OCR + optional VLM candidate и формирует schema-compliant JSON.

5. `Grounding`
   Для каждого поля пытается найти evidence: страницу, `bbox`, текстовый фрагмент, движок и исходный регион.

6. `Validation`
   Проверяет локальные и cross-field ограничения: даты, суммы, валюты, line items, согласованность итогов.

7. `Confidence`
   Сводит сигналы OCR, extraction, grounding, validation и document quality в field-level и document-level confidence.

8. `Routing`
   На основе confidence и объяснимых причин переводит поля и документ в `accepted`, `needs_review` или `rejected`.

9. `Review`
   Создаёт задачи только по спорным полям и предоставляет reviewer UI с evidence и возможностью исправления.

10. `Storage / Persistence`
    Сохраняет результаты в PostgreSQL и JSON-артефакты, подготавливая основу для evaluation и active learning.

## Слои приложения

### API layer

FastAPI предоставляет внешний HTTP-контур:
- загрузка документов;
- получение статуса;
- выдача финального результата;
- review UI и review submit;
- запуск evaluation.

API не содержит provider-specific логики. Он вызывает сервисы orchestration и работает только с типизированными request/response моделями.

### Service layer

В слое `services` находятся orchestration-сценарии:
- `DocumentPipelineService`
- `ReviewService`
- `EvaluationService`

Именно здесь соединяются независимые модули, но без жёсткой привязки к конкретным OCR/VLM провайдерам.

### Domain modules

- `parsing`
- `ocr`
- `vlm`
- `extraction`
- `grounding`
- `validation`
- `confidence`
- `routing`

Каждый модуль имеет собственные интерфейсы и небольшие реализации. Это позволяет benchmark’ить и заменять компоненты по отдельности.

### Persistence layer

SQLAlchemy models описывают реляционную модель данных. Alembic фиксирует схему миграциями. Артефакты документа и промежуточные JSON сохраняются через `storage` abstraction.

## Внутренние контракты

Ключевой формат для parsing:

- `ParsedDocument`
- `ParsedPage`
- `Region`
- `Span`
- `TableRegion`

Ключевой формат для extraction:

- `ExtractionFieldResult`
- `FieldEvidence`
- `ValidationReport`
- `RoutedField`
- `DocumentResult`

Контракты намеренно отделены от ORM-моделей. Это позволяет:
- безопасно версионировать API;
- строить offline evaluation;
- хранить артефакты как JSON;
- использовать разные движки без переписывания БД.

## OCR и VLM adapters

### OCR

OCR backend реализует унифицированный интерфейс:
- вход: документ/страница;
- выход: список `OCRSpan` c текстом, `bbox`, confidence и metadata.

В MVP baseline adapter ориентирован на локально воспроизводимое извлечение текста из digital-born PDF через PyMuPDF text layer. Для photographed documents архитектура готова к подключению RapidOCR/Tesseract/PaddleOCR без изменения downstream-модулей.

### VLM

VLM backend не является обязательным в MVP-пути. Он предназначен для:
- fallback на сложных документах;
- сравнения OCR-vs-VLM;
- future ensemble routing.

В текущем коде есть stub-интерфейс и точка расширения под реальные провайдеры.

## Confidence-aware routing

Routing строится на explainable причинах:
- низкое покрытие OCR;
- отсутствие grounding;
- ошибки валидации;
- расхождение между engine outputs;
- низкий общий quality score документа.

Это позволяет:
- минимизировать ручную проверку;
- поддерживать SLA-подобные пороги;
- измерять `auto-accept rate` и `review rate`.

## Review workflow

Review UI показывает только поля, которые действительно спорны. Reviewer видит:
- изображение/страницу;
- candidate value;
- validation status;
- evidence text и `bbox`;
- сырые OCR span’ы.

Результаты review сохраняются так, чтобы затем использовать их для:
- анализа качества;
- обучения улучшенных правил;
- будущего active learning dataset generation.

## Эволюция к V2/V3

Архитектура уже сейчас подготовлена к:
- schema registry;
- VLM fallback adapter;
- multilingual extraction;
- benchmark suite;
- analytics dashboard;
- active learning loop.

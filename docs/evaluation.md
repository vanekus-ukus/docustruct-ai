# Evaluation

## Почему нужен field-aware evaluation

Для Document AI недостаточно измерять только exact-match на уровне всего JSON-документа. Ошибки в одном поле и в line items имеют разную стоимость. Кроме того, система должна учитывать:
- omission;
- hallucination;
- schema-invalid output;
- unsupported routing;
- долю review;
- auto-accept rate.

## Режимы сравнения полей

Поддерживаемые стратегии:

- `exact`
  Для ID, invoice number, кодов и дискретных полей.

- `numeric_tolerance`
  Для сумм и налогов с допустимой погрешностью.

- `date_equivalence`
  Для дат в разных, но эквивалентных форматах.

- `fuzzy_text`
  Для имён контрагентов и текстовых полей.

- `array_match`
  Для `line_items` и массивов сущностей.

## Метрики

На уровне поля:
- precision;
- recall;
- exact accuracy;
- grounded accuracy;
- validation pass rate.

На уровне документа:
- schema validity rate;
- supported rate;
- review rate;
- auto-accept rate;
- reject rate.

На уровне сегмента:
- document type;
- input quality band;
- scanned vs photographed vs digital-born;
- engine family;
- route outcome.

## Артефакты evaluation

Каждый запуск evaluation сохраняет:
- JSON summary;
- Markdown summary;
- агрегаты по типу документа;
- агрегаты по полям;
- список типовых failure modes.

## CLI benchmark

Для offline benchmark без HTTP-слоя можно использовать:

```bash
python scripts/run_benchmark.py \
  --input examples/evaluation/invoice_benchmark.json \
  --name invoice-local-benchmark \
  --document-type invoice
```

CLI:
- читает JSON-массив evaluation items;
- создаёт запись в `evaluation_runs`;
- сохраняет `summary.json` и `summary.md` в artifact storage.

## Сравнение двух прогонов

Для сравнения baseline и candidate summary можно использовать:

```bash
python scripts/compare_benchmarks.py \
  --baseline benchmark_artifacts/evaluation/ocr-only/summary.json \
  --candidate benchmark_artifacts/evaluation/ocr-plus-vlm/summary.json
```

Скрипт возвращает:
- delta по `overall_accuracy`;
- delta по каждому полю;
- удобную основу для `ocr_only vs ocr_plus_vlm` анализа.

## Использование результатов

Evaluation предназначен не только для отчётности, но и для:
- сравнения OCR/VLM backends;
- сравнения extraction-стратегий;
- настройки routing thresholds;
- отбора данных для future active learning pipeline.

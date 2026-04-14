# Roadmap

## V1

- ingestion для PDF/PNG/JPG/JPEG;
- local storage abstraction;
- parsing contracts;
- baseline OCR adapter;
- schema-first extraction для `invoice`;
- grounding, validation, confidence, routing;
- minimal review UI;
- PostgreSQL persistence;
- field-aware evaluation.

## V2

- полноценный multi-document-type registry;
- provider-backed VLM fallback adapter;
- реальный remote/provider integration поверх mock provider contract;
- улучшенный parsing photographed documents;
- table structure recovery и line item reconstruction;
- benchmark scripts;
- reviewer analytics;
- better document quality scoring.

## V3

- OCR + VLM ensemble;
- multilingual support;
- analytics dashboard;
- active learning feedback loop;
- engine comparison by cost/latency/quality;
- schema registry UI;
- multi-tenant configuration;
- extended human-in-the-loop orchestration.

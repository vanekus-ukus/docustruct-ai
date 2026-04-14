from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from docustruct_ai.db.base import Base
from docustruct_ai.evaluation.service import EvaluationService
from docustruct_ai.extraction.registry import DocumentSchemaRegistry
from docustruct_ai.storage.adapters.local import LocalFileStorage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Запуск offline benchmark/evaluation для docustruct-ai")
    parser.add_argument("--input", required=True, help="Путь к JSON-файлу с evaluation items")
    parser.add_argument("--name", required=True, help="Имя evaluation run")
    parser.add_argument("--document-type", required=True, help="Тип документа: invoice/act/contract")
    parser.add_argument("--database-url", default="sqlite:///./benchmark.db", help="SQLAlchemy database URL")
    parser.add_argument("--artifacts-root", default="./benchmark_artifacts", help="Каталог для JSON/Markdown отчётов")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise SystemExit("Файл benchmark должен содержать JSON-массив items")

    engine = create_engine(
        args.database_url,
        future=True,
        connect_args={"check_same_thread": False} if args.database_url.startswith("sqlite") else {},
    )
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        service = EvaluationService(
            registry=DocumentSchemaRegistry(),
            artifact_storage=LocalFileStorage(Path(args.artifacts_root)),
        )
        run = service.run(
            db=session,
            name=args.name,
            document_type=args.document_type,
            items=payload,
        )
        print(
            json.dumps(
                {
                    "evaluation_run_id": run.id,
                    "status": run.status,
                    "overall_accuracy": run.summary_json.get("overall_accuracy"),
                    "documents_total": run.summary_json.get("documents_total"),
                    "report_path": run.report_path,
                },
                ensure_ascii=False,
            )
        )
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())

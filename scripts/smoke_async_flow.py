from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./smoke_async.db")
os.environ.setdefault("STORAGE_ROOT", "./smoke_async_data/storage")
os.environ.setdefault("ARTIFACTS_ROOT", "./smoke_async_data/artifacts")
os.environ.setdefault("EXECUTION_MODE", "async")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("CELERY_TASK_EAGER_PROPAGATES", "true")

from docustruct_ai.api.routes.documents import get_document_result, get_document_status, upload_document
from docustruct_ai.config import get_settings
from docustruct_ai.db.base import Base
from docustruct_ai.db.session import SessionLocal, engine
from docustruct_ai.models import Document
from docustruct_ai.services.factory import (
    get_ingestion_service,
    get_pipeline_service,
    get_query_service,
)
from docustruct_ai.services.worker import celery_app

from scripts.smoke_api_flow import GENERATED, FIXTURES, render_fixture_pdf


def main() -> None:
    get_settings.cache_clear()
    get_ingestion_service.cache_clear()
    get_pipeline_service.cache_clear()
    get_query_service.cache_clear()
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        payload = json.loads((FIXTURES / "invoice_demo.json").read_text(encoding="utf-8"))
        pdf_path = GENERATED / "invoice_demo_async.pdf"
        render_fixture_pdf(payload, pdf_path)

        with pdf_path.open("rb") as fh:
            upload = UploadFile(file=fh, filename=pdf_path.name)
            response = upload_document(
                file=upload,
                document_type="invoice",
                external_id="async-invoice-demo",
                db=db,
                ingestion_service=get_ingestion_service(),
                pipeline_service=get_pipeline_service(),
            )

        query = get_query_service()
        status = get_document_status(response.document_id, db=db, query_service=query)
        result = get_document_result(response.document_id, db=db, query_service=query)
        document = db.execute(select(Document).where(Document.id == response.document_id)).scalar_one()
        print(
            json.dumps(
                {
                    "document_id": response.document_id,
                    "upload_status": response.status,
                    "job_id": response.job_id,
                    "worker_task_id": response.worker_task_id,
                    "document_status": document.status,
                    "job_status": status.latest_job_status,
                    "route": result.route,
                },
                ensure_ascii=False,
            )
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()

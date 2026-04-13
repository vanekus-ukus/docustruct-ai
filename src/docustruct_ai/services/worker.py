from __future__ import annotations

from celery import Celery

from docustruct_ai.config import get_settings
from docustruct_ai.db.session import SessionLocal
from docustruct_ai.services.factory import get_pipeline_service

settings = get_settings()
celery_app = Celery("docustruct_ai", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(name="docustruct_ai.process_document")
def process_document_task(document_id: str, job_id: str | None = None) -> dict[str, str]:
    db = SessionLocal()
    try:
        result = get_pipeline_service().run(db, document_id=document_id, job_id=job_id)
        return {"document_id": result.document_id, "route": result.route}
    finally:
        db.close()

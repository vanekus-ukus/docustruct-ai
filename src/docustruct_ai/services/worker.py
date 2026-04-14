from __future__ import annotations

from celery import Celery
from celery.result import AsyncResult

from docustruct_ai.config import get_settings
from docustruct_ai.db.session import SessionLocal
from docustruct_ai.services.factory import get_pipeline_service

settings = get_settings()
celery_app = Celery("docustruct_ai", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=settings.celery_task_eager_propagates,
)


def enqueue_document_task(document_id: str, job_id: str) -> AsyncResult:
    return process_document_task.delay(document_id, job_id)


@celery_app.task(name="docustruct_ai.process_document")
def process_document_task(document_id: str, job_id: str | None = None) -> dict[str, str]:
    db = SessionLocal()
    try:
        result = get_pipeline_service().run(db, document_id=document_id, job_id=job_id)
        return {"document_id": result.document_id, "route": result.route}
    finally:
        db.close()

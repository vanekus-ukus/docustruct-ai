from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from docustruct_ai.api.schemas import HealthResponse
from docustruct_ai.config import get_settings
from docustruct_ai.db.session import get_db
from docustruct_ai.services.factory import get_query_service

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    database = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database = "error"
    storage = "ok" if get_settings().storage_root.exists() else "error"
    status = "ok" if database == "ok" and storage == "ok" else "degraded"
    return HealthResponse(app=get_settings().app_name, status=status, database=database, storage=storage)


@router.get("/metrics", response_class=PlainTextResponse)
def metrics(db: Session = Depends(get_db), query_service=Depends(get_query_service)) -> str:
    data = query_service.count_metrics(db)
    lines = [
        "# TYPE docustruct_documents_total gauge",
        f"docustruct_documents_total {data['documents_total']}",
        "# TYPE docustruct_review_tasks_open gauge",
        f"docustruct_review_tasks_open {data['review_tasks_open']}",
        "# TYPE docustruct_accepted_documents gauge",
        f"docustruct_accepted_documents {data['accepted_documents']}",
        "# TYPE docustruct_rejected_documents gauge",
        f"docustruct_rejected_documents {data['rejected_documents']}",
    ]
    return "\n".join(lines)

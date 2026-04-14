from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from docustruct_ai.api.schemas import (
    DocumentResponse,
    DocumentResultResponse,
    DocumentStatusResponse,
    UploadResponse,
)
from docustruct_ai.config import get_settings
from docustruct_ai.db.session import get_db
from docustruct_ai.services.factory import (
    get_ingestion_service,
    get_pipeline_service,
    get_query_service,
)
from docustruct_ai.services.worker import enqueue_document_task

router = APIRouter(prefix="/documents", tags=["documents"])
templates = Jinja2Templates(directory=str(get_settings().templates_dir))


@router.post("/upload", response_model=UploadResponse)
def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    external_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
    ingestion_service=Depends(get_ingestion_service),
    pipeline_service=Depends(get_pipeline_service),
) -> UploadResponse:
    if document_type not in {"invoice", "act", "contract"}:
        raise HTTPException(status_code=400, detail="Unsupported document_type")
    filename = (file.filename or "").lower()
    if not filename.endswith((".pdf", ".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Unsupported file format")
    document, job = ingestion_service.create_document(db, file, document_type, external_id)

    if get_settings().execution_mode == "inline":
        pipeline_service.run(db, document.id, job.id)
        db.refresh(job)
        status = "completed"
        worker_task_id = None
    else:
        task = enqueue_document_task(document.id, job.id)
        job.worker_task_id = task.id
        db.commit()
        db.refresh(job)
        status = "queued"
        worker_task_id = task.id
    return UploadResponse(
        document_id=document.id,
        job_id=job.id,
        worker_task_id=worker_task_id,
        status=status,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    query_service=Depends(get_query_service),
) -> DocumentResponse:
    document = query_service.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(**query_service.serialize_document(document))


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
    query_service=Depends(get_query_service),
) -> DocumentStatusResponse:
    document = query_service.get_document_with_result(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentStatusResponse(**query_service.serialize_status(document))


@router.get("/{document_id}/result", response_model=DocumentResultResponse)
def get_document_result(
    document_id: str,
    db: Session = Depends(get_db),
    query_service=Depends(get_query_service),
) -> DocumentResultResponse:
    document = query_service.get_document_with_result(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResultResponse(**query_service.serialize_result(document))


@router.get("/{document_id}/review", response_class=HTMLResponse)
def review_document(
    document_id: str,
    request: Request,
    db: Session = Depends(get_db),
    query_service=Depends(get_query_service),
) -> HTMLResponse:
    document = query_service.get_document_with_result(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    context = query_service.build_review_context(document)
    context["request"] = request
    return templates.TemplateResponse("review_document.html", context)


@router.get("/{document_id}/pages/{page_number}/image")
def get_document_page_image(
    document_id: str,
    page_number: int,
    db: Session = Depends(get_db),
    query_service=Depends(get_query_service),
) -> FileResponse:
    page_path = query_service.get_page_path(db, document_id, page_number)
    if not page_path or not Path(page_path).exists():
        raise HTTPException(status_code=404, detail="Page image not found")
    return FileResponse(page_path)

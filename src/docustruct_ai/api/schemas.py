from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class UploadResponse(BaseModel):
    document_id: str
    job_id: str
    worker_task_id: str | None = None
    status: str


class DocumentResponse(BaseModel):
    id: str
    external_id: str | None
    document_type: str
    filename: str
    status: str
    routing_state: str
    confidence_score: float | None = None
    quality_score: float | None = None
    metadata: dict[str, Any]


class DocumentStatusResponse(BaseModel):
    document_id: str
    status: str
    routing_state: str
    job_id: str | None = None
    worker_task_id: str | None = None
    latest_job_status: str | None = None
    error_message: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    confidence_score: float | None = None


class DocumentResultResponse(BaseModel):
    document_id: str
    document_type: str
    schema_name: str
    payload: dict[str, Any]
    fields: list[dict[str, Any]]
    validation_issues: list[dict[str, Any]]
    confidence: float
    route: str
    routing_reasons: list[str]
    metadata: dict[str, Any]


class ReviewSubmitRequest(BaseModel):
    decision: str
    final_value: str | None = None
    reviewer: str | None = None
    comment: str | None = None


class ReviewSubmitResponse(BaseModel):
    review_task_id: int
    status: str
    decision: str


class EvaluationItemRequest(BaseModel):
    document_id: str
    prediction: dict[str, Any]
    ground_truth: dict[str, Any]


class EvaluationRunRequest(BaseModel):
    name: str
    document_type: str
    items: list[EvaluationItemRequest]


class EvaluationRunResponse(BaseModel):
    evaluation_run_id: int
    status: str
    summary: dict[str, Any]


class HealthResponse(BaseModel):
    app: str
    status: str
    database: str
    storage: str

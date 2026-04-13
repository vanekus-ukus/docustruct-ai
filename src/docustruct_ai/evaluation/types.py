from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvaluationSummary(BaseModel):
    name: str
    document_type: str
    documents_total: int
    overall_accuracy: float
    field_metrics: dict[str, dict[str, Any]] = Field(default_factory=dict)

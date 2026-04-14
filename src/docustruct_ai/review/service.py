from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from docustruct_ai.config import Settings
from docustruct_ai.models import Document, ExtractedEntity, ExtractedField, ReviewDecision, ReviewTask
from docustruct_ai.utils.normalization import (
    normalize_currency,
    normalize_date,
    normalize_number,
    normalize_whitespace,
)


class ReviewService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def submit(
        self,
        db: Session,
        task_id: int,
        decision: str,
        final_value: str | None,
        reviewer: str | None,
        comment: str | None,
    ) -> ReviewTask:
        task = db.execute(select(ReviewTask).where(ReviewTask.id == task_id)).scalar_one()
        field = db.execute(select(ExtractedField).where(ExtractedField.id == task.field_id)).scalar_one_or_none()
        document = db.execute(select(Document).where(Document.id == task.document_id)).scalar_one()

        task.status = "completed"
        task.completed_at = datetime.utcnow()

        if field is not None:
            if decision == "accept":
                field.routing_state = "accepted"
                field.confidence = max(field.confidence, self.settings.accept_threshold)
            elif decision == "edit":
                normalized_value = self._normalize_field_value(field, final_value)
                field.value_text = None if normalized_value is None else str(normalized_value)
                field.normalized_value = normalized_value
                field.routing_state = "accepted"
                field.confidence = max(field.confidence, self.settings.accept_threshold)
            elif decision == "unsupported":
                field.value_text = None
                field.normalized_value = None
                field.routing_state = "rejected"
                field.confidence = min(field.confidence, self.settings.reject_threshold)

            entity = field.entity
            if entity is not None:
                payload = dict(entity.payload_json)
                payload[field.field_name] = field.normalized_value
                entity.payload_json = payload
        elif decision == "unsupported":
            document.routing_state = "rejected"
            document.status = "reviewed"

        db.add(
            ReviewDecision(
                review_task_id=task.id,
                decision=decision,
                final_value=final_value,
                reviewer=reviewer,
                comment=comment,
            )
        )
        db.flush()

        open_tasks = db.execute(
            select(ReviewTask).where(ReviewTask.document_id == task.document_id).where(ReviewTask.status == "open")
        ).scalars().all()
        if open_tasks:
            document.routing_state = "needs_review"
            document.status = "review_pending"
        else:
            routes = db.execute(
                select(ExtractedField.routing_state)
                .join(ExtractedEntity, ExtractedEntity.id == ExtractedField.entity_id)
                .where(ExtractedEntity.document_id == task.document_id)
            ).scalars().all()
            if routes and all(route == "accepted" for route in routes):
                document.routing_state = "accepted"
                document.status = "reviewed"
            elif any(route == "rejected" for route in routes):
                document.routing_state = "rejected"
                document.status = "reviewed"
            else:
                document.routing_state = "needs_review"
                document.status = "reviewed"

        db.commit()
        db.refresh(task)
        return task

    def _normalize_field_value(self, field: ExtractedField, final_value: str | None) -> str | float | None:
        if final_value is None:
            return None
        if field.value_type in {"number", "integer"}:
            return normalize_number(final_value)
        lowered_name = field.field_name.lower()
        if "date" in lowered_name:
            return normalize_date(final_value)
        if lowered_name == "currency":
            return normalize_currency(final_value) or normalize_whitespace(final_value)
        return normalize_whitespace(final_value)

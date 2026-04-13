from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from docustruct_ai.config import Settings
from docustruct_ai.models import Document, ExtractedEntity, ExtractedField, ReviewDecision, ReviewTask


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
                field.value_text = final_value
                field.normalized_value = final_value
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

        db.add(
            ReviewDecision(
                review_task_id=task.id,
                decision=decision,
                final_value=final_value,
                reviewer=reviewer,
                comment=comment,
            )
        )

        open_tasks = db.execute(
            select(ReviewTask).where(ReviewTask.document_id == task.document_id).where(ReviewTask.status == "open")
        ).scalars().all()
        if not open_tasks:
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

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from docustruct_ai.models import (
    Document,
    ExtractedEntity,
    ExtractedField,
    FieldEvidenceModel,
    Job,
    OCRSpan,
    Page,
    ReviewTask,
    ValidationReport,
)


class DocumentQueryService:
    def get_document(self, db: Session, document_id: str) -> Document | None:
        statement = select(Document).where(Document.id == document_id)
        return db.execute(statement).scalar_one_or_none()

    def get_document_with_result(self, db: Session, document_id: str) -> Document | None:
        statement = (
            select(Document)
            .where(Document.id == document_id)
            .options(
                selectinload(Document.jobs),
                selectinload(Document.pages),
                selectinload(Document.review_tasks),
                selectinload(Document.entities)
                .selectinload(ExtractedEntity.fields)
                .selectinload(ExtractedField.evidence_items),
                selectinload(Document.entities)
                .selectinload(ExtractedEntity.fields)
                .selectinload(ExtractedField.validation_reports),
                selectinload(Document.validation_reports),
                selectinload(Document.ocr_spans),
            )
        )
        return db.execute(statement).scalar_one_or_none()

    def serialize_document(self, document: Document) -> dict[str, Any]:
        return {
            "id": document.id,
            "external_id": document.external_id,
            "document_type": document.document_type,
            "filename": document.filename,
            "status": document.status,
            "routing_state": document.routing_state,
            "confidence_score": document.confidence_score,
            "quality_score": document.quality_score,
            "metadata": document.metadata_json,
        }

    def serialize_status(self, document: Document) -> dict[str, Any]:
        latest_job = (
            sorted(
                document.jobs,
                key=lambda item: item.started_at or item.finished_at or document.updated_at,
            )[-1]
            if document.jobs
            else None
        )
        return {
            "document_id": document.id,
            "status": document.status,
            "routing_state": document.routing_state,
            "latest_job_status": latest_job.status if latest_job else None,
            "confidence_score": document.confidence_score,
        }

    def serialize_result(self, document: Document) -> dict[str, Any]:
        entity = sorted(document.entities, key=lambda item: item.created_at)[-1] if document.entities else None
        if not entity:
            return {
                "document_id": document.id,
                "document_type": document.document_type,
                "schema_name": document.document_type,
                "payload": {},
                "fields": [],
                "validation_issues": [],
                "confidence": document.confidence_score or 0.0,
                "route": document.routing_state,
                "routing_reasons": [],
                "metadata": {},
            }

        field_reports = {field.id: field.validation_reports for field in entity.fields}
        fields = []
        for field in entity.fields:
            evidence = field.evidence_items[0] if field.evidence_items else None
            fields.append(
                {
                    "field_name": field.field_name,
                    "value": field.normalized_value if field.normalized_value is not None else field.value_text,
                    "normalized_value": field.normalized_value,
                    "value_type": field.value_type,
                    "confidence": field.confidence,
                    "required": field.is_required,
                    "route": field.routing_state,
                    "evidence": self._serialize_evidence(evidence),
                    "validation_issues": [self._serialize_validation(item) for item in field_reports.get(field.id, [])],
                    "alternatives": field.metadata_json.get("alternatives", []),
                    "metadata": field.metadata_json,
                }
            )
        document_issues = [
            self._serialize_validation(issue)
            for issue in document.validation_reports
            if issue.scope == "document"
        ]
        return {
            "document_id": document.id,
            "document_type": document.document_type,
            "schema_name": entity.schema_name,
            "payload": entity.payload_json,
            "fields": fields,
            "validation_issues": document_issues,
            "confidence": document.confidence_score or 0.0,
            "route": document.routing_state,
            "routing_reasons": document.metadata_json.get("routing_reasons", []),
            "metadata": {"quality_score": document.quality_score},
        }

    def build_review_context(self, document: Document) -> dict[str, Any]:
        entity = sorted(document.entities, key=lambda item: item.created_at)[-1] if document.entities else None
        fields_by_id = {field.id: field for field in entity.fields} if entity else {}
        pages = sorted(document.pages, key=lambda page: page.page_number)
        ocr_text_by_page: dict[int, str] = {}
        grouped_spans: dict[int, list[str]] = {}
        for span in sorted(document.ocr_spans, key=lambda item: (item.page_id, item.reading_order)):
            page = next((page for page in pages if page.id == span.page_id), None)
            if not page:
                continue
            grouped_spans.setdefault(page.page_number, []).append(span.text)
        for page_number, parts in grouped_spans.items():
            ocr_text_by_page[page_number] = " ".join(parts)

        tasks = []
        for task in sorted(
            [item for item in document.review_tasks if item.status == "open"], key=lambda item: item.id
        ):
            field = fields_by_id.get(task.field_id) if task.field_id is not None else None
            evidence = field.evidence_items[0] if field and field.evidence_items else None
            tasks.append(
                {
                    "id": task.id,
                    "status": task.status,
                    "reason": task.reason,
                    "candidate_value": task.candidate_value,
                    "field_name": field.field_name if field else None,
                    "validation_issues": [
                        self._serialize_validation(item)
                        for item in (
                            field.validation_reports
                            if field
                            else [report for report in document.validation_reports if report.scope == "document"]
                        )
                    ],
                    "evidence": self._serialize_evidence(evidence),
                    "value_type": field.value_type if field else "document",
                    "required": field.is_required if field else False,
                }
            )

        return {
            "document": document,
            "pages": [
                {
                    "page_number": page.page_number,
                    "image_url": f"/documents/{document.id}/pages/{page.page_number}/image",
                    "ocr_text": ocr_text_by_page.get(page.page_number, ""),
                }
                for page in pages
            ],
            "tasks": tasks,
        }

    def get_page_path(self, db: Session, document_id: str, page_number: int) -> str | None:
        statement = (
            select(Page)
            .where(Page.document_id == document_id)
            .where(Page.page_number == page_number)
        )
        page = db.execute(statement).scalar_one_or_none()
        return page.image_path if page else None

    def count_metrics(self, db: Session) -> dict[str, int]:
        documents = db.query(Document).count()
        review_open = db.query(ReviewTask).filter(ReviewTask.status == "open").count()
        accepted = db.query(Document).filter(Document.routing_state == "accepted").count()
        rejected = db.query(Document).filter(Document.routing_state == "rejected").count()
        return {
            "documents_total": documents,
            "review_tasks_open": review_open,
            "accepted_documents": accepted,
            "rejected_documents": rejected,
        }

    def _serialize_evidence(self, evidence: FieldEvidenceModel | None) -> dict[str, Any] | None:
        if not evidence:
            return None
        return {
            "page": evidence.page_number,
            "bbox": evidence.bbox_json,
            "evidence_text": evidence.evidence_text,
            "source_engine": evidence.source_engine,
            "source_region_id": evidence.source_region_id,
            "grounding_score": evidence.grounding_score,
        }

    def _serialize_validation(self, issue: ValidationReport) -> dict[str, Any]:
        field_name = None
        if issue.field_id is not None and issue.field is not None:
            field_name = issue.field.field_name
        return {
            "scope": issue.scope,
            "field_name": field_name,
            "status": issue.status,
            "rule_name": issue.rule_name,
            "message": issue.message,
            "details": issue.details_json,
        }

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from docustruct_ai.config import Settings
from docustruct_ai.confidence.service import ConfidenceService
from docustruct_ai.core.types import DocumentResult, ExtractionFieldResult
from docustruct_ai.extraction.orchestrator import ExtractionOrchestrator
from docustruct_ai.extraction.registry import DocumentSchemaRegistry
from docustruct_ai.grounding.service import GroundingService
from docustruct_ai.models import (
    Document,
    EngineRun,
    ExtractedEntity,
    ExtractedField,
    FieldEvidenceModel,
    Job,
    OCRSpan,
    Page,
    ParsedRegion,
    ReviewDecision,
    ReviewTask,
    ValidationReport,
)
from docustruct_ai.ocr.interfaces import OCRBackend
from docustruct_ai.parsing.interfaces import ParsingBackend
from docustruct_ai.routing.service import RoutingService
from docustruct_ai.storage.base import ArtifactStorage
from docustruct_ai.validation.service import ValidationService
from docustruct_ai.vlm.interfaces import VLMBackend


class DocumentPipelineService:
    def __init__(
        self,
        settings: Settings,
        artifact_storage: ArtifactStorage,
        parser: ParsingBackend,
        ocr_backend: OCRBackend,
        vlm_backend: VLMBackend,
        extractor: ExtractionOrchestrator,
        registry: DocumentSchemaRegistry,
        grounding_service: GroundingService,
        validation_service: ValidationService,
        confidence_service: ConfidenceService,
        routing_service: RoutingService,
    ) -> None:
        self.settings = settings
        self.artifact_storage = artifact_storage
        self.parser = parser
        self.ocr_backend = ocr_backend
        self.vlm_backend = vlm_backend
        self.extractor = extractor
        self.registry = registry
        self.grounding_service = grounding_service
        self.validation_service = validation_service
        self.confidence_service = confidence_service
        self.routing_service = routing_service

    def run(self, db: Session, document_id: str, job_id: str | None = None) -> DocumentResult:
        document = db.execute(select(Document).where(Document.id == document_id)).scalar_one()
        job = db.execute(select(Job).where(Job.id == job_id)).scalar_one_or_none() if job_id else None

        try:
            self._set_job_started(db, document, job)
            self._cleanup_previous_results(db, document.id)

            parsed_document = self.parser.parse(document)
            self._persist_parsed_document(db, document.id, parsed_document)
            self._record_engine_run(
                db,
                document.id,
                job_id,
                engine_type="parsing",
                engine_name=parsed_document.metadata.get("engine_name", "parser"),
                output_payload=parsed_document.model_dump(),
            )

            ocr_spans, ocr_metadata = self.ocr_backend.extract(document)
            self._persist_ocr_spans(db, document.id, ocr_spans)
            self._record_engine_run(
                db,
                document.id,
                job_id,
                engine_type="ocr",
                engine_name=ocr_metadata.get("engine_name", "ocr"),
                engine_version=ocr_metadata.get("engine_version"),
                output_payload={"span_count": len(ocr_spans), "metadata": ocr_metadata},
                metrics_json={"coverage_score": ocr_metadata.get("coverage_score", 0.0)},
            )

            schema = self.registry.get(document.document_type)
            vlm_candidate = self.vlm_backend.extract_candidate(
                document=document,
                document_type=document.document_type,
                target_schema=schema.json_schema(),
                instructions=schema.instructions,
            )
            candidate_payload = self.extractor.extract(document.document_type, parsed_document, ocr_spans, vlm_candidate)
            normalized_payload = schema.model.model_validate(candidate_payload).model_dump()

            validation_issues = self.validation_service.validate(document.document_type, normalized_payload)
            document_quality_score = self._document_quality(parsed_document, ocr_metadata)
            field_results = self._build_field_results(schema, normalized_payload, ocr_spans, validation_issues, document_quality_score)

            doc_result = DocumentResult(
                document_id=document.id,
                document_type=document.document_type,
                schema_name=schema.name,
                payload=normalized_payload,
                fields=field_results,
                validation_issues=validation_issues,
                confidence=0.0,
                route="needs_review",
                routing_reasons=[],
                metadata={"quality_score": document_quality_score},
            )
            doc_result.confidence = self.confidence_service.score_document(field_results, validation_issues)
            doc_result.route, doc_result.routing_reasons = self.routing_service.route_document(doc_result)

            self._persist_result(db, document, doc_result, job_id)
            artifact_payload = doc_result.model_dump()
            artifact_path = self.artifact_storage.save_json(f"{document.id}/result.json", artifact_payload)
            document.metadata_json = {
                **document.metadata_json,
                "result_artifact_path": artifact_path,
                "routing_reasons": doc_result.routing_reasons,
            }
            document.status = "processed"
            document.routing_state = doc_result.route
            document.confidence_score = doc_result.confidence
            document.quality_score = document_quality_score

            self._set_job_finished(db, job)
            db.commit()
            db.refresh(document)
            return doc_result
        except Exception as exc:
            document.status = "failed"
            document.metadata_json = {**document.metadata_json, "pipeline_error": str(exc)}
            if job:
                job.status = "failed"
                job.error_message = str(exc)
                job.finished_at = datetime.utcnow()
            db.commit()
            raise

    def _build_field_results(
        self,
        schema: Any,
        payload: dict[str, Any],
        spans: list[Any],
        validation_issues: list[Any],
        document_quality_score: float,
    ) -> list[ExtractionFieldResult]:
        fields: list[ExtractionFieldResult] = []
        for field_def in schema.fields:
            value = payload.get(field_def.name)
            field_validation_issues = [
                issue for issue in validation_issues if issue.field_name == field_def.name
            ]
            result = ExtractionFieldResult(
                field_name=field_def.name,
                value=value,
                normalized_value=value,
                value_type=self._value_type(value),
                required=field_def.required,
                evidence=self.grounding_service.ground(field_def.name, value, spans),
                validation_issues=field_validation_issues,
            )
            result.confidence = self.confidence_service.score_field(
                result, document_quality_score, validation_issues
            )
            result.route, route_reasons = self.routing_service.route_field(result)
            result.metadata["route_reasons"] = route_reasons
            fields.append(result)
        return fields

    def _persist_result(
        self,
        db: Session,
        document: Document,
        result: DocumentResult,
        job_id: str | None,
    ) -> None:
        entity = ExtractedEntity(
            document_id=document.id,
            schema_name=result.schema_name,
            schema_version="1.0",
            payload_json=result.payload,
        )
        db.add(entity)
        db.flush()

        for field in result.fields:
            field_model = ExtractedField(
                entity_id=entity.id,
                field_name=field.field_name,
                value_text=None if isinstance(field.value, (dict, list)) else str(field.value) if field.value is not None else None,
                normalized_value=field.normalized_value,
                value_type=field.value_type,
                confidence=field.confidence,
                routing_state=field.route,
                is_required=field.required,
                metadata_json=field.metadata,
            )
            db.add(field_model)
            db.flush()

            if field.evidence:
                db.add(
                    FieldEvidenceModel(
                        field_id=field_model.id,
                        page_number=field.evidence.page,
                        bbox_json=field.evidence.bbox,
                        evidence_text=field.evidence.evidence_text,
                        source_engine=field.evidence.source_engine,
                        source_region_id=field.evidence.source_region_id,
                        grounding_score=field.evidence.grounding_score,
                    )
                )

            for issue in field.validation_issues:
                db.add(
                    ValidationReport(
                        document_id=document.id,
                        field_id=field_model.id,
                        scope=issue.scope,
                        status=issue.status,
                        rule_name=issue.rule_name,
                        message=issue.message,
                        details_json=issue.details,
                    )
                )

            if field.route == "needs_review":
                db.add(
                    ReviewTask(
                        document_id=document.id,
                        field_id=field_model.id,
                        status="open",
                        reason=", ".join(field.metadata.get("route_reasons", [])),
                        candidate_value=str(field.value) if field.value is not None else None,
                    )
                )

        for issue in result.validation_issues:
            if issue.scope == "document":
                db.add(
                    ValidationReport(
                        document_id=document.id,
                        field_id=None,
                        scope=issue.scope,
                        status=issue.status,
                        rule_name=issue.rule_name,
                        message=issue.message,
                        details_json=issue.details,
                    )
                )

        has_field_review = any(field.route == "needs_review" for field in result.fields)
        if result.route == "needs_review" and not has_field_review:
            document_issue_reasons = [
                issue.message for issue in result.validation_issues if issue.scope == "document"
            ]
            review_reason_parts = document_issue_reasons or result.routing_reasons or ["document_review_required"]
            db.add(
                ReviewTask(
                    document_id=document.id,
                    field_id=None,
                    status="open",
                    reason=" | ".join(review_reason_parts),
                    candidate_value=None,
                )
            )

        self._record_engine_run(
            db,
            document.id,
            job_id,
            engine_type="extraction",
            engine_name="schema_orchestrator",
            output_payload=result.model_dump(),
            metrics_json={"document_confidence": result.confidence, "route": result.route},
        )

    def _persist_parsed_document(self, db: Session, document_id: str, parsed_document: Any) -> None:
        page_map = {
            page.page_number: page.id
            for page in db.execute(select(Page).where(Page.document_id == document_id)).scalars()
        }
        for page in parsed_document.pages:
            page_id = page_map.get(page.page_number)
            if page_id is None:
                continue
            for region in page.regions:
                db.add(
                    ParsedRegion(
                        document_id=document_id,
                        page_id=page_id,
                        region_type=region.kind,
                        bbox_json=region.bbox.as_list(),
                        text=region.text,
                        reading_order=region.reading_order,
                        metadata_json=region.metadata,
                    )
                )
        artifact = parsed_document.model_dump()
        self.artifact_storage.save_json(f"{document_id}/parsed_document.json", artifact)

    def _persist_ocr_spans(self, db: Session, document_id: str, spans: list[Any]) -> None:
        page_map = {
            page.page_number: page.id
            for page in db.execute(select(Page).where(Page.document_id == document_id)).scalars()
        }
        for order, span in enumerate(spans):
            page_id = page_map.get(span.page)
            if page_id is None:
                continue
            db.add(
                OCRSpan(
                    document_id=document_id,
                    page_id=page_id,
                    span_type=span.level,
                    text=span.text,
                    bbox_json=span.bbox.as_list(),
                    confidence=span.confidence,
                    source_engine=span.source_engine,
                    reading_order=order,
                    metadata_json=span.metadata,
                )
            )
        self.artifact_storage.save_json(
            f"{document_id}/ocr_spans.json",
            {"spans": [span.model_dump() for span in spans]},
        )

    def _record_engine_run(
        self,
        db: Session,
        document_id: str,
        job_id: str | None,
        engine_type: str,
        engine_name: str,
        engine_version: str | None = None,
        input_payload: dict[str, Any] | None = None,
        output_payload: dict[str, Any] | None = None,
        metrics_json: dict[str, Any] | None = None,
    ) -> None:
        db.add(
            EngineRun(
                document_id=document_id,
                job_id=job_id,
                engine_type=engine_type,
                engine_name=engine_name,
                engine_version=engine_version,
                status="ok",
                input_payload=input_payload or {},
                output_payload=output_payload or {},
                metrics_json=metrics_json or {},
            )
        )

    def _cleanup_previous_results(self, db: Session, document_id: str) -> None:
        review_task_ids = list(
            db.execute(select(ReviewTask.id).where(ReviewTask.document_id == document_id)).scalars()
        )
        if review_task_ids:
            db.execute(delete(ReviewDecision).where(ReviewDecision.review_task_id.in_(review_task_ids)))
        db.execute(delete(ReviewTask).where(ReviewTask.document_id == document_id))
        db.execute(delete(ValidationReport).where(ValidationReport.document_id == document_id))
        db.execute(delete(OCRSpan).where(OCRSpan.document_id == document_id))
        db.execute(delete(ParsedRegion).where(ParsedRegion.document_id == document_id))
        entity_ids = list(
            db.execute(select(ExtractedEntity.id).where(ExtractedEntity.document_id == document_id)).scalars()
        )
        if entity_ids:
            field_ids = list(
                db.execute(select(ExtractedField.id).where(ExtractedField.entity_id.in_(entity_ids))).scalars()
            )
            if field_ids:
                db.execute(delete(FieldEvidenceModel).where(FieldEvidenceModel.field_id.in_(field_ids)))
            db.execute(delete(ExtractedField).where(ExtractedField.entity_id.in_(entity_ids)))
            db.execute(delete(ExtractedEntity).where(ExtractedEntity.id.in_(entity_ids)))
        db.commit()

    def _set_job_started(self, db: Session, document: Document, job: Job | None) -> None:
        document.status = "processing"
        if job:
            job.status = "running"
            job.started_at = datetime.utcnow()
        db.commit()

    def _set_job_finished(self, db: Session, job: Job | None) -> None:
        if job:
            job.status = "completed"
            job.finished_at = datetime.utcnow()

    def _document_quality(self, parsed_document: Any, ocr_metadata: dict[str, Any]) -> float:
        region_count = sum(len(page.regions) for page in parsed_document.pages)
        pages = max(len(parsed_document.pages), 1)
        structure_score = min(1.0, region_count / (8 * pages))
        ocr_score = float(ocr_metadata.get("coverage_score", 0.0))
        return round((0.45 * structure_score) + (0.55 * ocr_score), 4)

    def _value_type(self, value: Any) -> str:
        if isinstance(value, list):
            return "array"
        if isinstance(value, dict):
            return "object"
        if isinstance(value, float):
            return "number"
        if isinstance(value, int):
            return "integer"
        return "string"

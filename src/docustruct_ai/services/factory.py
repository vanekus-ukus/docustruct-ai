from __future__ import annotations

from functools import lru_cache

from docustruct_ai.config import get_settings
from docustruct_ai.confidence.service import ConfidenceService
from docustruct_ai.evaluation.service import EvaluationService
from docustruct_ai.extraction.orchestrator import ExtractionOrchestrator
from docustruct_ai.extraction.registry import DocumentSchemaRegistry
from docustruct_ai.grounding.service import GroundingService
from docustruct_ai.ingestion.service import IngestionService
from docustruct_ai.ocr.pymupdf_adapter import PyMuPDFTextOcrAdapter
from docustruct_ai.parsing.heuristic_parser import HeuristicParser
from docustruct_ai.review.service import ReviewService
from docustruct_ai.routing.service import RoutingService
from docustruct_ai.services.documents import DocumentQueryService
from docustruct_ai.services.pipeline import DocumentPipelineService
from docustruct_ai.storage.adapters.local import LocalFileStorage
from docustruct_ai.validation.service import ValidationService
from docustruct_ai.vlm.stub import StubVLMBackend


@lru_cache(maxsize=1)
def get_registry() -> DocumentSchemaRegistry:
    return DocumentSchemaRegistry()


@lru_cache(maxsize=1)
def get_source_storage() -> LocalFileStorage:
    return LocalFileStorage(get_settings().storage_root)


@lru_cache(maxsize=1)
def get_artifact_storage() -> LocalFileStorage:
    return LocalFileStorage(get_settings().artifacts_root)


@lru_cache(maxsize=1)
def get_ingestion_service() -> IngestionService:
    return IngestionService(get_source_storage())


@lru_cache(maxsize=1)
def get_pipeline_service() -> DocumentPipelineService:
    registry = get_registry()
    return DocumentPipelineService(
        settings=get_settings(),
        artifact_storage=get_artifact_storage(),
        parser=HeuristicParser(),
        ocr_backend=PyMuPDFTextOcrAdapter(),
        vlm_backend=StubVLMBackend(),
        extractor=ExtractionOrchestrator(registry),
        registry=registry,
        grounding_service=GroundingService(),
        validation_service=ValidationService(registry),
        confidence_service=ConfidenceService(),
        routing_service=RoutingService(get_settings()),
    )


@lru_cache(maxsize=1)
def get_review_service() -> ReviewService:
    return ReviewService(get_settings())


@lru_cache(maxsize=1)
def get_query_service() -> DocumentQueryService:
    return DocumentQueryService()


@lru_cache(maxsize=1)
def get_evaluation_service() -> EvaluationService:
    return EvaluationService(get_registry(), get_artifact_storage())

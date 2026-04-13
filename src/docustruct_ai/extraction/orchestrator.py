from __future__ import annotations

from typing import Any

from docustruct_ai.core.types import ParsedDocument, Span
from docustruct_ai.extraction.invoice import InvoiceExtractor
from docustruct_ai.extraction.registry import DocumentSchemaRegistry


class ExtractionOrchestrator:
    def __init__(self, registry: DocumentSchemaRegistry) -> None:
        self.registry = registry
        self.invoice_extractor = InvoiceExtractor()

    def extract(
        self,
        document_type: str,
        parsed_document: ParsedDocument,
        spans: list[Span],
        vlm_candidate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if document_type == "invoice":
            return self.invoice_extractor.extract(parsed_document, spans, vlm_candidate)

        # MVP fallback for act/contract: schema-valid but low-confidence extraction.
        return self.registry.get(document_type).model().model_dump()

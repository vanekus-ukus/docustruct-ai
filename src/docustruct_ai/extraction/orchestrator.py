from __future__ import annotations

from typing import Any

from docustruct_ai.extraction.act import ActExtractor
from docustruct_ai.extraction.contract import ContractExtractor
from docustruct_ai.core.types import ParsedDocument, Span
from docustruct_ai.extraction.invoice import InvoiceExtractor
from docustruct_ai.extraction.registry import DocumentSchemaRegistry


class ExtractionOrchestrator:
    def __init__(self, registry: DocumentSchemaRegistry) -> None:
        self.registry = registry
        self.invoice_extractor = InvoiceExtractor()
        self.act_extractor = ActExtractor()
        self.contract_extractor = ContractExtractor()

    def extract(
        self,
        document_type: str,
        parsed_document: ParsedDocument,
        spans: list[Span],
        vlm_candidate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if document_type == "invoice":
            return self.invoice_extractor.extract(parsed_document, spans, vlm_candidate)
        if document_type == "act":
            return self.act_extractor.extract(parsed_document, spans, vlm_candidate)
        if document_type == "contract":
            return self.contract_extractor.extract(parsed_document, spans, vlm_candidate)

        return self.registry.get(document_type).model().model_dump()

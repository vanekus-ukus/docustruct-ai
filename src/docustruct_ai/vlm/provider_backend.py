from __future__ import annotations

from typing import Any

from docustruct_ai.models import Document
from docustruct_ai.vlm.interfaces import VLMBackend
from docustruct_ai.vlm.providers import VLMProvider


class ProviderVLMBackend(VLMBackend):
    def __init__(self, provider: VLMProvider, backend_name: str = "provider_vlm") -> None:
        self.provider = provider
        self.backend_name = backend_name

    def extract_candidate(
        self,
        document: Document,
        document_type: str,
        target_schema: dict[str, Any],
        instructions: str,
    ) -> dict[str, Any] | None:
        return self.provider.generate_candidate(
            document=document,
            document_type=document_type,
            target_schema=target_schema,
            instructions=instructions,
        )

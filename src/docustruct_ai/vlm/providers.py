from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from docustruct_ai.models import Document


class VLMProvider(ABC):
    @abstractmethod
    def generate_candidate(
        self,
        document: Document,
        document_type: str,
        target_schema: dict[str, Any],
        instructions: str,
    ) -> dict[str, Any] | None:
        """Return a provider-level candidate payload."""


class MockVLMProvider(VLMProvider):
    def generate_candidate(
        self,
        document: Document,
        document_type: str,
        target_schema: dict[str, Any],
        instructions: str,
    ) -> dict[str, Any] | None:
        candidate = document.metadata_json.get("vlm_candidate")
        if isinstance(candidate, dict):
            return candidate
        template_candidates = document.metadata_json.get("vlm_template_candidates", {})
        if isinstance(template_candidates, dict):
            provider_candidate = template_candidates.get(document_type)
            if isinstance(provider_candidate, dict):
                return provider_candidate
        return None

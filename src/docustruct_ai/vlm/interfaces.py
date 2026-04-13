from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from docustruct_ai.models import Document


class VLMBackend(ABC):
    @abstractmethod
    def extract_candidate(
        self,
        document: Document,
        document_type: str,
        target_schema: dict[str, Any],
        instructions: str,
    ) -> dict[str, Any] | None:
        """Return an optional candidate payload for hard documents."""

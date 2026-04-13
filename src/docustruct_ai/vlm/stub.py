from __future__ import annotations

from typing import Any

from docustruct_ai.models import Document
from docustruct_ai.vlm.interfaces import VLMBackend


class StubVLMBackend(VLMBackend):
    def extract_candidate(
        self,
        document: Document,
        document_type: str,
        target_schema: dict[str, Any],
        instructions: str,
    ) -> dict[str, Any] | None:
        return None

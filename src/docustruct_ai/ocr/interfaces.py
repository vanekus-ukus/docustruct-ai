from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from docustruct_ai.core.types import Span
from docustruct_ai.models import Document


class OCRBackend(ABC):
    @abstractmethod
    def extract(self, document: Document) -> tuple[list[Span], dict[str, Any]]:
        """Return OCR spans and engine metadata."""

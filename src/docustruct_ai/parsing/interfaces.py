from __future__ import annotations

from abc import ABC, abstractmethod

from docustruct_ai.core.types import ParsedDocument
from docustruct_ai.models import Document


class ParsingBackend(ABC):
    @abstractmethod
    def parse(self, document: Document) -> ParsedDocument:
        """Parse document into a structured layout representation."""

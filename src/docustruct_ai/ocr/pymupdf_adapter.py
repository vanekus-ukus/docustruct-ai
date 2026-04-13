from __future__ import annotations

from typing import Any

import fitz

from docustruct_ai.core.types import BoundingBox, Span
from docustruct_ai.models import Document
from docustruct_ai.ocr.interfaces import OCRBackend


class PyMuPDFTextOcrAdapter(OCRBackend):
    engine_name = "pymupdf-text"
    engine_version = fitz.VersionBind

    def extract(self, document: Document) -> tuple[list[Span], dict[str, Any]]:
        spans: list[Span] = []
        page_word_counts: dict[int, int] = {}
        source = fitz.open(document.source_path)
        try:
            for page_index, page in enumerate(source):
                words = page.get_text("words")
                page_word_counts[page_index + 1] = len(words)
                for order, word in enumerate(words):
                    x1, y1, x2, y2, text, *_ = word
                    if not str(text).strip():
                        continue
                    spans.append(
                        Span(
                            id=f"ocr-{page_index + 1}-{order}",
                            page=page_index + 1,
                            text=str(text).strip(),
                            bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                            confidence=0.92,
                            source_engine=self.engine_name,
                            level="word",
                            metadata={"page_index": page_index},
                        )
                    )
        finally:
            source.close()

        total_words = sum(page_word_counts.values())
        metadata: dict[str, Any] = {
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "page_word_counts": page_word_counts,
            "coverage_score": 0.9 if total_words else 0.0,
        }
        return spans, metadata

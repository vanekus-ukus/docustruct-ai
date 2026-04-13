from __future__ import annotations

from docustruct_ai.core.types import BoundingBox, FieldEvidence, Span
from docustruct_ai.utils.normalization import normalize_whitespace
from docustruct_ai.utils.text import fuzzy_similarity


class GroundingService:
    def ground(self, field_name: str, value: object, spans: list[Span]) -> FieldEvidence | None:
        if value is None:
            return None
        if isinstance(value, list):
            return None

        target = normalize_whitespace(str(value))
        if not target:
            return None

        best_span: Span | None = None
        best_score = 0.0
        for span in spans:
            score = self._match_score(target, span.text)
            if score > best_score:
                best_score = score
                best_span = span

        if not best_span or best_score < 0.55:
            return None

        bbox = BoundingBox(
            x1=best_span.bbox.x1,
            y1=best_span.bbox.y1,
            x2=best_span.bbox.x2,
            y2=best_span.bbox.y2,
        )
        return FieldEvidence(
            page=best_span.page,
            bbox=bbox.as_list(),
            evidence_text=best_span.text,
            source_engine=best_span.source_engine,
            source_region_id=best_span.id,
            grounding_score=round(best_score, 4),
        )

    def _match_score(self, target: str, source: str) -> float:
        if target == source:
            return 1.0
        if target.lower() == source.lower():
            return 0.96
        if target.lower() in source.lower() or source.lower() in target.lower():
            return 0.82
        return fuzzy_similarity(target, source)

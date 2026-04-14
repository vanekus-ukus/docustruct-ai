from __future__ import annotations

import re
from typing import Any

from docustruct_ai.core.types import Span
from docustruct_ai.utils.normalization import normalize_number, normalize_whitespace


class LineExtractionSupport:
    def build_lines(self, spans: list[Span]) -> list[str]:
        grouped: dict[tuple[int, int], list[Span]] = {}
        for span in spans:
            line_key = (span.page, int(span.bbox.y1 // 12))
            grouped.setdefault(line_key, []).append(span)

        lines: list[str] = []
        for key in sorted(grouped.keys()):
            sorted_spans = sorted(grouped[key], key=lambda item: item.bbox.x1)
            line = " ".join(span.text for span in sorted_spans)
            cleaned = normalize_whitespace(line)
            if cleaned:
                lines.append(cleaned)
        return lines

    def merge_vlm_candidate(
        self, candidate: dict[str, Any], vlm_candidate: dict[str, Any] | None
    ) -> dict[str, Any]:
        if not vlm_candidate:
            return candidate
        merged = dict(candidate)
        for key, value in vlm_candidate.items():
            if merged.get(key) in (None, "", []):
                merged[key] = value
        return merged

    def extract_labeled_text(self, lines: list[str], labels: list[str]) -> str | None:
        for line in lines:
            lowered = line.lower()
            for label in labels:
                if label in lowered and ":" in line:
                    value = line.split(":", 1)[1].strip()
                    return normalize_whitespace(value)
        return None

    def extract_amount(self, lines: list[str], labels: list[str]) -> float | None:
        for line in lines:
            lowered = line.lower()
            for label in labels:
                if label in lowered:
                    amount_match = re.search(r"(-?\d[\d\s.,]*)", line)
                    if amount_match:
                        return normalize_number(amount_match.group(1))
        return None

    def extract_pattern(self, text: str, patterns: list[str]) -> str | None:
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                candidate = normalize_whitespace(match.group(1))
                validated = self.validate_identifier_candidate(candidate)
                if validated:
                    return validated
        return None

    def validate_identifier_candidate(self, candidate: str | None) -> str | None:
        if not candidate:
            return None
        cleaned = normalize_whitespace(candidate).strip(":")
        if not re.search(r"\d", cleaned):
            return None
        return cleaned

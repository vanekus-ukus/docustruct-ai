from __future__ import annotations

from typing import Any

from docustruct_ai.core.types import ParsedDocument, Span
from docustruct_ai.extraction.support import LineExtractionSupport
from docustruct_ai.utils.normalization import normalize_currency, normalize_date


class ActExtractor(LineExtractionSupport):
    label_variants = {
        "seller_name": ["исполнитель", "seller", "provider"],
        "buyer_name": ["заказчик", "buyer", "customer"],
        "act_date": ["дата акта", "дата", "act date"],
        "total": ["итого", "сумма", "total"],
    }

    number_patterns = [
        r"(?:акт)\s*(?:№|number|no)?\s*([A-ZА-Я0-9\-\/]+)",
    ]

    def extract(
        self,
        parsed_document: ParsedDocument,
        spans: list[Span],
        vlm_candidate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del parsed_document
        lines = self.build_lines(spans)
        text = "\n".join(lines)

        candidate = {
            "act_number": self.extract_pattern(text, self.number_patterns),
            "act_date": normalize_date(self.extract_labeled_text(lines, self.label_variants["act_date"])),
            "seller_name": self.extract_labeled_text(lines, self.label_variants["seller_name"]),
            "buyer_name": self.extract_labeled_text(lines, self.label_variants["buyer_name"]),
            "total": self.extract_amount(lines, self.label_variants["total"]),
            "currency": normalize_currency(text),
        }
        return self.merge_vlm_candidate(candidate, vlm_candidate)

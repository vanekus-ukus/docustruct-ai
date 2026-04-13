from __future__ import annotations

from typing import Any

from docustruct_ai.core.types import ParsedDocument, Span
from docustruct_ai.extraction.support import LineExtractionSupport
from docustruct_ai.utils.normalization import normalize_currency, normalize_date


class ContractExtractor(LineExtractionSupport):
    label_variants = {
        "party_a": ["сторона а", "party a"],
        "party_b": ["сторона б", "party b"],
        "contract_date": ["дата договора", "дата", "contract date"],
        "total_amount": ["общая сумма", "итого", "total amount"],
    }

    number_patterns = [
        r"(?:договор|contract)\s*(?:№|number|no)?\s*([A-ZА-Я0-9\-\/]+)",
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
            "contract_number": self.extract_pattern(text, self.number_patterns),
            "contract_date": normalize_date(
                self.extract_labeled_text(lines, self.label_variants["contract_date"])
            ),
            "party_a": self.extract_labeled_text(lines, self.label_variants["party_a"]),
            "party_b": self.extract_labeled_text(lines, self.label_variants["party_b"]),
            "total_amount": self.extract_amount(lines, self.label_variants["total_amount"]),
            "currency": normalize_currency(text),
        }
        return self.merge_vlm_candidate(candidate, vlm_candidate)

from __future__ import annotations

import re
from typing import Any

from docustruct_ai.core.types import ParsedDocument, Span
from docustruct_ai.extraction.schemas import InvoiceLineItem
from docustruct_ai.utils.normalization import (
    normalize_currency,
    normalize_date,
    normalize_number,
    normalize_whitespace,
)


class InvoiceExtractor:
    label_variants = {
        "supplier_name": ["поставщик", "supplier", "seller", "исполнитель"],
        "buyer_name": ["покупатель", "buyer", "customer", "заказчик"],
        "invoice_number": ["счет", "счёт", "invoice", "invoice number", "номер"],
        "invoice_date": ["дата счета", "дата счёта", "invoice date", "дата"],
        "due_date": ["срок оплаты", "оплатить до", "due date"],
        "subtotal": ["subtotal", "подытог", "сумма без ндс", "итого без налога"],
        "tax": ["ндс", "vat", "tax"],
        "total": ["итого к оплате", "итого", "total", "amount due"],
    }

    def extract(
        self,
        parsed_document: ParsedDocument,
        spans: list[Span],
        vlm_candidate: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        lines = self._build_lines(spans)
        text = "\n".join(lines)

        supplier_name = self._extract_labeled_text(lines, self.label_variants["supplier_name"])
        buyer_name = self._extract_labeled_text(lines, self.label_variants["buyer_name"])
        invoice_number = self._extract_invoice_number(text)
        invoice_date = normalize_date(self._extract_labeled_text(lines, self.label_variants["invoice_date"]))
        due_date = normalize_date(self._extract_labeled_text(lines, self.label_variants["due_date"]))
        subtotal = self._extract_amount(lines, self.label_variants["subtotal"])
        tax = self._extract_amount(lines, self.label_variants["tax"])
        total = self._extract_amount(lines, self.label_variants["total"])
        currency = normalize_currency(text)
        line_items = self._extract_line_items(lines)

        candidate = {
            "supplier_name": supplier_name,
            "buyer_name": buyer_name,
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "currency": currency,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "line_items": [item.model_dump() for item in line_items],
        }

        if vlm_candidate:
            candidate = self._merge_vlm_candidate(candidate, vlm_candidate)

        return candidate

    def _merge_vlm_candidate(
        self, candidate: dict[str, Any], vlm_candidate: dict[str, Any]
    ) -> dict[str, Any]:
        merged = dict(candidate)
        for key, value in vlm_candidate.items():
            if merged.get(key) in (None, "", []):
                merged[key] = value
        return merged

    def _build_lines(self, spans: list[Span]) -> list[str]:
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

    def _extract_labeled_text(self, lines: list[str], labels: list[str]) -> str | None:
        for line in lines:
            lowered = line.lower()
            for label in labels:
                if label in lowered and ":" in line:
                    value = line.split(":", 1)[1].strip()
                    return normalize_whitespace(value)
        return None

    def _extract_invoice_number(self, text: str) -> str | None:
        patterns = [
            r"(?:счет|сч[её]т|invoice)(?:\s*(?:number|no|№))?\s*[:#]?\s*([A-ZА-Я0-9\-\/]+)",
            r"(?:номер)\s*[:#]?\s*([A-ZА-Я0-9\-\/]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_amount(self, lines: list[str], labels: list[str]) -> float | None:
        for line in lines:
            lowered = line.lower()
            for label in labels:
                if label in lowered:
                    amount_match = re.search(r"(-?\d[\d\s.,]*)", line)
                    if amount_match:
                        return normalize_number(amount_match.group(1))
        return None

    def _extract_line_items(self, lines: list[str]) -> list[InvoiceLineItem]:
        items: list[InvoiceLineItem] = []
        for line in lines:
            match = re.match(
                r"^\s*\d+\s+(.+?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s*$",
                line,
            )
            if not match:
                continue
            description, quantity, unit_price, total = match.groups()
            items.append(
                InvoiceLineItem(
                    description=normalize_whitespace(description),
                    quantity=normalize_number(quantity),
                    unit_price=normalize_number(unit_price),
                    total=normalize_number(total),
                )
            )
        return items

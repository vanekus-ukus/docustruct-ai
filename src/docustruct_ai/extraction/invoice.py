from __future__ import annotations

import re
from typing import Any

from docustruct_ai.core.types import ParsedDocument, Span
from docustruct_ai.extraction.schemas import InvoiceLineItem
from docustruct_ai.extraction.support import LineExtractionSupport
from docustruct_ai.utils.normalization import (
    normalize_currency,
    normalize_date,
    normalize_number,
    normalize_whitespace,
)


class InvoiceExtractor(LineExtractionSupport):
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
        del parsed_document
        lines = self.build_lines(spans)
        text = "\n".join(lines)

        supplier_name = self.extract_labeled_text(lines, self.label_variants["supplier_name"])
        buyer_name = self.extract_labeled_text(lines, self.label_variants["buyer_name"])
        invoice_number = self._extract_invoice_number(text)
        invoice_date = normalize_date(self.extract_labeled_text(lines, self.label_variants["invoice_date"]))
        due_date = normalize_date(self.extract_labeled_text(lines, self.label_variants["due_date"]))
        subtotal = self.extract_amount(lines, self.label_variants["subtotal"])
        tax = self.extract_amount(lines, self.label_variants["tax"])
        total = self.extract_amount(lines, self.label_variants["total"])
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

        return self.merge_vlm_candidate(candidate, vlm_candidate)

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

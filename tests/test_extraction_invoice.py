from __future__ import annotations

from docustruct_ai.core.types import BoundingBox, ParsedDocument, ParsedPage, Span
from docustruct_ai.extraction.invoice import InvoiceExtractor


def test_invoice_extractor_extracts_core_fields() -> None:
    spans = [
        Span(id="1", page=1, text="Счет", bbox=BoundingBox(x1=0, y1=0, x2=10, y2=10), source_engine="test"),
        Span(id="2", page=1, text="№", bbox=BoundingBox(x1=12, y1=0, x2=15, y2=10), source_engine="test"),
        Span(id="3", page=1, text="INV-2024-001", bbox=BoundingBox(x1=16, y1=0, x2=35, y2=10), source_engine="test"),
        Span(id="4", page=1, text="Поставщик:", bbox=BoundingBox(x1=0, y1=20, x2=20, y2=30), source_engine="test"),
        Span(id="5", page=1, text="ООО", bbox=BoundingBox(x1=21, y1=20, x2=30, y2=30), source_engine="test"),
        Span(id="6", page=1, text="Альфа", bbox=BoundingBox(x1=31, y1=20, x2=50, y2=30), source_engine="test"),
        Span(id="7", page=1, text="Покупатель:", bbox=BoundingBox(x1=0, y1=40, x2=25, y2=50), source_engine="test"),
        Span(id="8", page=1, text="ООО", bbox=BoundingBox(x1=26, y1=40, x2=35, y2=50), source_engine="test"),
        Span(id="9", page=1, text="Бета", bbox=BoundingBox(x1=36, y1=40, x2=50, y2=50), source_engine="test"),
        Span(id="10", page=1, text="Дата", bbox=BoundingBox(x1=0, y1=60, x2=10, y2=70), source_engine="test"),
        Span(id="11", page=1, text="счета:", bbox=BoundingBox(x1=12, y1=60, x2=28, y2=70), source_engine="test"),
        Span(id="12", page=1, text="17.05.2024", bbox=BoundingBox(x1=29, y1=60, x2=45, y2=70), source_engine="test"),
        Span(id="13", page=1, text="Валюта:", bbox=BoundingBox(x1=0, y1=80, x2=15, y2=90), source_engine="test"),
        Span(id="14", page=1, text="RUB", bbox=BoundingBox(x1=16, y1=80, x2=25, y2=90), source_engine="test"),
        Span(id="15", page=1, text="Подытог:", bbox=BoundingBox(x1=0, y1=100, x2=20, y2=110), source_engine="test"),
        Span(id="16", page=1, text="5500.00", bbox=BoundingBox(x1=21, y1=100, x2=35, y2=110), source_engine="test"),
        Span(id="17", page=1, text="НДС:", bbox=BoundingBox(x1=0, y1=120, x2=10, y2=130), source_engine="test"),
        Span(id="18", page=1, text="1100.00", bbox=BoundingBox(x1=11, y1=120, x2=25, y2=130), source_engine="test"),
        Span(id="19", page=1, text="Итого", bbox=BoundingBox(x1=0, y1=140, x2=10, y2=150), source_engine="test"),
        Span(id="20", page=1, text="к", bbox=BoundingBox(x1=11, y1=140, x2=13, y2=150), source_engine="test"),
        Span(id="21", page=1, text="оплате:", bbox=BoundingBox(x1=14, y1=140, x2=28, y2=150), source_engine="test"),
        Span(id="22", page=1, text="6600.00", bbox=BoundingBox(x1=29, y1=140, x2=43, y2=150), source_engine="test"),
    ]
    parsed_document = ParsedDocument(document_id="doc-1", pages=[ParsedPage(page_number=1, width=100, height=100)])

    payload = InvoiceExtractor().extract(parsed_document, spans)

    assert payload["invoice_number"] == "INV-2024-001"
    assert payload["invoice_date"] == "2024-05-17"
    assert payload["supplier_name"] == "ООО Альфа"
    assert payload["buyer_name"] == "ООО Бета"
    assert payload["currency"] == "RUB"
    assert payload["subtotal"] == 5500.0
    assert payload["tax"] == 1100.0
    assert payload["total"] == 6600.0

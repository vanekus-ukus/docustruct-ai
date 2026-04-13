from __future__ import annotations

from docustruct_ai.core.types import BoundingBox, ParsedDocument, ParsedPage, Span
from docustruct_ai.extraction.act import ActExtractor
from docustruct_ai.extraction.contract import ContractExtractor


def test_act_extractor_extracts_core_fields() -> None:
    spans = [
        Span(id="1", page=1, text="Акт", bbox=BoundingBox(x1=0, y1=0, x2=10, y2=10), source_engine="test"),
        Span(id="2", page=1, text="№", bbox=BoundingBox(x1=12, y1=0, x2=14, y2=10), source_engine="test"),
        Span(id="3", page=1, text="ACT-2024-008", bbox=BoundingBox(x1=15, y1=0, x2=35, y2=10), source_engine="test"),
        Span(id="4", page=1, text="Исполнитель:", bbox=BoundingBox(x1=0, y1=20, x2=20, y2=30), source_engine="test"),
        Span(id="5", page=1, text="ООО", bbox=BoundingBox(x1=21, y1=20, x2=30, y2=30), source_engine="test"),
        Span(id="6", page=1, text="Альфа", bbox=BoundingBox(x1=31, y1=20, x2=45, y2=30), source_engine="test"),
        Span(id="7", page=1, text="Поставка", bbox=BoundingBox(x1=46, y1=20, x2=62, y2=30), source_engine="test"),
        Span(id="8", page=1, text="Заказчик:", bbox=BoundingBox(x1=0, y1=40, x2=18, y2=50), source_engine="test"),
        Span(id="9", page=1, text="ООО", bbox=BoundingBox(x1=19, y1=40, x2=26, y2=50), source_engine="test"),
        Span(id="10", page=1, text="Бета", bbox=BoundingBox(x1=27, y1=40, x2=40, y2=50), source_engine="test"),
        Span(id="11", page=1, text="Маркет", bbox=BoundingBox(x1=41, y1=40, x2=58, y2=50), source_engine="test"),
        Span(id="12", page=1, text="Дата:", bbox=BoundingBox(x1=0, y1=60, x2=10, y2=70), source_engine="test"),
        Span(id="13", page=1, text="2024-05-20", bbox=BoundingBox(x1=11, y1=60, x2=28, y2=70), source_engine="test"),
        Span(id="14", page=1, text="Итого:", bbox=BoundingBox(x1=0, y1=80, x2=12, y2=90), source_engine="test"),
        Span(id="15", page=1, text="6600.00", bbox=BoundingBox(x1=13, y1=80, x2=25, y2=90), source_engine="test"),
        Span(id="16", page=1, text="RUB", bbox=BoundingBox(x1=26, y1=80, x2=33, y2=90), source_engine="test"),
    ]
    parsed_document = ParsedDocument(document_id="act-1", pages=[ParsedPage(page_number=1, width=100, height=100)])

    payload = ActExtractor().extract(parsed_document, spans)

    assert payload["act_number"] == "ACT-2024-008"
    assert payload["act_date"] == "2024-05-20"
    assert payload["seller_name"] == "ООО Альфа Поставка"
    assert payload["buyer_name"] == "ООО Бета Маркет"
    assert payload["currency"] == "RUB"
    assert payload["total"] == 6600.0


def test_contract_extractor_extracts_core_fields() -> None:
    spans = [
        Span(id="1", page=1, text="Договор", bbox=BoundingBox(x1=0, y1=0, x2=14, y2=10), source_engine="test"),
        Span(id="2", page=1, text="№", bbox=BoundingBox(x1=15, y1=0, x2=17, y2=10), source_engine="test"),
        Span(id="3", page=1, text="CTR-2024-042", bbox=BoundingBox(x1=18, y1=0, x2=38, y2=10), source_engine="test"),
        Span(id="4", page=1, text="Сторона", bbox=BoundingBox(x1=0, y1=20, x2=15, y2=30), source_engine="test"),
        Span(id="5", page=1, text="А:", bbox=BoundingBox(x1=16, y1=20, x2=20, y2=30), source_engine="test"),
        Span(id="6", page=1, text="ООО", bbox=BoundingBox(x1=21, y1=20, x2=28, y2=30), source_engine="test"),
        Span(id="7", page=1, text="Альфа", bbox=BoundingBox(x1=29, y1=20, x2=42, y2=30), source_engine="test"),
        Span(id="8", page=1, text="Поставка", bbox=BoundingBox(x1=43, y1=20, x2=58, y2=30), source_engine="test"),
        Span(id="9", page=1, text="Сторона", bbox=BoundingBox(x1=0, y1=40, x2=15, y2=50), source_engine="test"),
        Span(id="10", page=1, text="Б:", bbox=BoundingBox(x1=16, y1=40, x2=20, y2=50), source_engine="test"),
        Span(id="11", page=1, text="ООО", bbox=BoundingBox(x1=21, y1=40, x2=28, y2=50), source_engine="test"),
        Span(id="12", page=1, text="Бета", bbox=BoundingBox(x1=29, y1=40, x2=40, y2=50), source_engine="test"),
        Span(id="13", page=1, text="Маркет", bbox=BoundingBox(x1=41, y1=40, x2=56, y2=50), source_engine="test"),
        Span(id="14", page=1, text="Дата", bbox=BoundingBox(x1=0, y1=60, x2=8, y2=70), source_engine="test"),
        Span(id="15", page=1, text="договора:", bbox=BoundingBox(x1=9, y1=60, x2=22, y2=70), source_engine="test"),
        Span(id="16", page=1, text="2024-04-01", bbox=BoundingBox(x1=23, y1=60, x2=39, y2=70), source_engine="test"),
        Span(id="17", page=1, text="Общая", bbox=BoundingBox(x1=0, y1=80, x2=10, y2=90), source_engine="test"),
        Span(id="18", page=1, text="сумма:", bbox=BoundingBox(x1=11, y1=80, x2=20, y2=90), source_engine="test"),
        Span(id="19", page=1, text="120000.00", bbox=BoundingBox(x1=21, y1=80, x2=35, y2=90), source_engine="test"),
        Span(id="20", page=1, text="RUB", bbox=BoundingBox(x1=36, y1=80, x2=43, y2=90), source_engine="test"),
    ]
    parsed_document = ParsedDocument(document_id="contract-1", pages=[ParsedPage(page_number=1, width=100, height=100)])

    payload = ContractExtractor().extract(parsed_document, spans)

    assert payload["contract_number"] == "CTR-2024-042"
    assert payload["contract_date"] == "2024-04-01"
    assert payload["party_a"] == "ООО Альфа Поставка"
    assert payload["party_b"] == "ООО Бета Маркет"
    assert payload["currency"] == "RUB"
    assert payload["total_amount"] == 120000.0

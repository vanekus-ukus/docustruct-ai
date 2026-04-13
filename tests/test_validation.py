from __future__ import annotations

from docustruct_ai.extraction.registry import DocumentSchemaRegistry
from docustruct_ai.validation.service import ValidationService


def test_invoice_validation_flags_total_mismatch() -> None:
    payload = {
        "supplier_name": "ООО Альфа",
        "buyer_name": "ООО Бета",
        "invoice_number": "INV-1",
        "invoice_date": "2024-05-17",
        "due_date": "2024-05-27",
        "currency": "RUB",
        "subtotal": 100.0,
        "tax": 20.0,
        "total": 150.0,
        "line_items": [{"description": "A", "quantity": 1, "unit_price": 100.0, "total": 100.0}],
    }
    service = ValidationService(DocumentSchemaRegistry())

    issues = service.validate("invoice", payload)

    assert any(issue.rule_name == "invoice_total_consistency" for issue in issues)

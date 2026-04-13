from __future__ import annotations

from docustruct_ai.config import Settings
from docustruct_ai.core.types import ExtractionFieldResult
from docustruct_ai.confidence.service import ConfidenceService
from docustruct_ai.routing.service import RoutingService


def test_field_routing_accepts_strong_field() -> None:
    field = ExtractionFieldResult(field_name="invoice_number", value="INV-1", required=True)
    field.confidence = ConfidenceService().score_field(field, document_quality_score=0.95, validation_issues=[])
    route, _ = RoutingService(Settings()).route_field(field)
    assert route in {"accepted", "needs_review"}


def test_field_routing_rejects_missing_required_field() -> None:
    field = ExtractionFieldResult(field_name="invoice_number", value=None, required=True)
    field.confidence = 0.1
    route, reasons = RoutingService(Settings()).route_field(field)
    assert route == "rejected"
    assert "below_reject_threshold" in reasons

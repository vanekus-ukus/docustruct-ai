from __future__ import annotations

from docustruct_ai.config import Settings
from docustruct_ai.core.types import DocumentResult, ExtractionFieldResult


class RoutingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def route_field(self, field: ExtractionFieldResult) -> tuple[str, list[str]]:
        reasons: list[str] = []
        has_validation_error = any(issue.status == "error" for issue in field.validation_issues)
        if field.value in (None, "", []):
            reasons.append("missing_value")
            if not field.required and not has_validation_error:
                reasons.append("optional_field_missing")
                return "accepted", reasons
            if field.required:
                reasons.append("required_field_missing")
                reasons.append("manual_review_required")
                return "needs_review", reasons
        if field.value_type != "array" and not field.evidence and field.value not in (None, "", []):
            reasons.append("missing_grounding")
        if has_validation_error:
            reasons.append("validation_error")

        if field.confidence >= self.settings.accept_threshold and "validation_error" not in reasons:
            return "accepted", reasons
        if field.confidence < self.settings.reject_threshold and field.required:
            reasons.append("below_reject_threshold")
            return "rejected", reasons
        reasons.append("manual_review_required")
        return "needs_review", reasons

    def route_document(self, result: DocumentResult) -> tuple[str, list[str]]:
        reasons = list(result.routing_reasons)
        rejected_required = any(
            field.required and field.route == "rejected" for field in result.fields
        )
        review_needed = any(field.route == "needs_review" for field in result.fields)

        if rejected_required or result.confidence < self.settings.reject_threshold:
            reasons.append("required_field_rejected_or_low_document_confidence")
            return "rejected", reasons
        if review_needed or result.confidence < self.settings.accept_threshold:
            reasons.append("field_review_needed_or_document_below_accept_threshold")
            return "needs_review", reasons
        reasons.append("all_required_fields_grounded_and_valid")
        return "accepted", reasons

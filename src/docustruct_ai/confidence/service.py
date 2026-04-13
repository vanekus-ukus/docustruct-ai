from __future__ import annotations

from collections import defaultdict
from typing import Any

from docustruct_ai.core.types import ExtractionFieldResult, ValidationIssue


class ConfidenceService:
    def score_field(
        self,
        field: ExtractionFieldResult,
        document_quality_score: float,
        validation_issues: list[ValidationIssue],
    ) -> float:
        score = 0.15
        if field.value not in (None, "", []):
            score += 0.35
        if field.value_type == "array" and field.value not in (None, "", []):
            score += 0.15
        if field.evidence:
            score += 0.2 * field.evidence.grounding_score
        score += 0.15 * document_quality_score

        field_errors = [issue for issue in validation_issues if issue.field_name == field.field_name]
        if field_errors:
            score -= 0.2
        else:
            score += 0.1

        if field.required and field.value in (None, "", []):
            score -= 0.2

        return max(0.0, min(1.0, round(score, 4)))

    def score_document(
        self, fields: list[ExtractionFieldResult], validation_issues: list[ValidationIssue]
    ) -> float:
        if not fields:
            return 0.0
        per_field = [field.confidence for field in fields]
        score = sum(per_field) / len(per_field)
        document_errors = [issue for issue in validation_issues if issue.scope == "document"]
        if document_errors:
            score -= 0.08 * len(document_errors)
        return max(0.0, min(1.0, round(score, 4)))

    def group_by_field(self, validation_issues: list[ValidationIssue]) -> dict[str, list[ValidationIssue]]:
        grouped: dict[str, list[ValidationIssue]] = defaultdict(list)
        for issue in validation_issues:
            grouped[issue.field_name or "__document__"].append(issue)
        return grouped

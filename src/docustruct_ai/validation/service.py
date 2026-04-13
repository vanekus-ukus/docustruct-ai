from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from docustruct_ai.core.types import ValidationIssue
from docustruct_ai.extraction.registry import DocumentSchemaRegistry
from docustruct_ai.utils.normalization import is_close, normalize_date, normalize_number


class ValidationService:
    def __init__(self, registry: DocumentSchemaRegistry) -> None:
        self.registry = registry

    def validate(self, document_type: str, payload: dict[str, Any]) -> list[ValidationIssue]:
        schema = self.registry.get(document_type)
        issues: list[ValidationIssue] = []

        try:
            schema.model.model_validate(payload)
        except ValidationError as exc:
            for error in exc.errors():
                field_name = ".".join(str(part) for part in error["loc"])
                issues.append(
                    ValidationIssue(
                        scope="field",
                        field_name=field_name,
                        status="error",
                        rule_name="schema_validation",
                        message=error["msg"],
                        details={"type": error["type"]},
                    )
                )

        field_map = schema.field_map()
        for field_name, field_def in field_map.items():
            value = payload.get(field_name)
            if field_def.required and value in (None, "", []):
                issues.append(
                    ValidationIssue(
                        scope="field",
                        field_name=field_name,
                        status="error",
                        rule_name="required_field",
                        message="Обязательное поле отсутствует.",
                    )
                )
            if "date" in field_def.validator_rules and value and not normalize_date(str(value)):
                issues.append(
                    ValidationIssue(
                        scope="field",
                        field_name=field_name,
                        status="error",
                        rule_name="date_format",
                        message="Поле не удалось нормализовать как дату.",
                    )
                )
            if "non_negative" in field_def.validator_rules and value is not None:
                number = normalize_number(value)
                if number is not None and number < 0:
                    issues.append(
                        ValidationIssue(
                            scope="field",
                            field_name=field_name,
                            status="error",
                            rule_name="non_negative",
                            message="Числовое поле не должно быть отрицательным.",
                        )
                    )

        if document_type == "invoice":
            issues.extend(self._validate_invoice(payload))

        return issues

    def _validate_invoice(self, payload: dict[str, Any]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        subtotal = normalize_number(payload.get("subtotal"))
        tax = normalize_number(payload.get("tax") or 0)
        total = normalize_number(payload.get("total"))
        if subtotal is not None and total is not None and not is_close(subtotal + (tax or 0), total):
            issues.append(
                ValidationIssue(
                    scope="document",
                    status="warning",
                    rule_name="invoice_total_consistency",
                    message="subtotal + tax не совпадает с total в допустимой погрешности.",
                    details={"subtotal": subtotal, "tax": tax, "total": total},
                )
            )

        line_items = payload.get("line_items") or []
        line_sum = 0.0
        counted = 0
        for item in line_items:
            if not isinstance(item, dict):
                continue
            value = normalize_number(item.get("total"))
            if value is None:
                continue
            counted += 1
            line_sum += value

        if counted and subtotal is not None and not is_close(line_sum, subtotal):
            issues.append(
                ValidationIssue(
                    scope="document",
                    status="warning",
                    rule_name="line_item_sum_consistency",
                    message="Сумма line_items расходится с subtotal.",
                    details={"line_sum": line_sum, "subtotal": subtotal},
                )
            )
        return issues

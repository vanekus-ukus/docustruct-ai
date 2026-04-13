from __future__ import annotations

from docustruct_ai.extraction.schemas import (
    ActSchema,
    ContractSchema,
    DocumentSchemaDefinition,
    InvoiceSchema,
    SchemaFieldDefinition,
)


class DocumentSchemaRegistry:
    def __init__(self) -> None:
        self._schemas = {
            "invoice": DocumentSchemaDefinition(
                name="invoice",
                version="1.0",
                model=InvoiceSchema,
                instructions="Извлекай счёт-фактуру или invoice по строгой схеме и не заполняй поля без evidence.",
                fields=[
                    SchemaFieldDefinition(
                        name="supplier_name",
                        required=True,
                        extraction_strategy="label_or_header_lookup",
                        validator_rules=["non_empty"],
                        scoring_type="fuzzy_text",
                    ),
                    SchemaFieldDefinition(
                        name="buyer_name",
                        required=True,
                        extraction_strategy="label_lookup",
                        validator_rules=["non_empty"],
                        scoring_type="fuzzy_text",
                    ),
                    SchemaFieldDefinition(
                        name="invoice_number",
                        required=True,
                        extraction_strategy="regex_plus_label_lookup",
                        validator_rules=["non_empty"],
                        scoring_type="exact",
                    ),
                    SchemaFieldDefinition(
                        name="invoice_date",
                        required=True,
                        extraction_strategy="date_regex",
                        validator_rules=["date"],
                        scoring_type="date_equivalence",
                    ),
                    SchemaFieldDefinition(
                        name="due_date",
                        required=False,
                        extraction_strategy="date_regex",
                        validator_rules=["date"],
                        scoring_type="date_equivalence",
                    ),
                    SchemaFieldDefinition(
                        name="currency",
                        required=True,
                        extraction_strategy="currency_symbol_detection",
                        validator_rules=["currency"],
                        scoring_type="exact",
                    ),
                    SchemaFieldDefinition(
                        name="subtotal",
                        required=True,
                        extraction_strategy="amount_lookup",
                        validator_rules=["non_negative"],
                        scoring_type="numeric_tolerance",
                    ),
                    SchemaFieldDefinition(
                        name="tax",
                        required=False,
                        extraction_strategy="amount_lookup",
                        validator_rules=["non_negative"],
                        scoring_type="numeric_tolerance",
                    ),
                    SchemaFieldDefinition(
                        name="total",
                        required=True,
                        extraction_strategy="amount_lookup",
                        validator_rules=["non_negative"],
                        scoring_type="numeric_tolerance",
                    ),
                    SchemaFieldDefinition(
                        name="line_items",
                        required=False,
                        extraction_strategy="table_heuristics",
                        validator_rules=["array"],
                        scoring_type="array_match",
                    ),
                ],
            ),
            "act": DocumentSchemaDefinition(
                name="act",
                version="1.0",
                model=ActSchema,
                instructions="Извлекай ключевые реквизиты акта, не выдумывай отсутствующие поля.",
                fields=[
                    SchemaFieldDefinition(name="act_number", required=True, extraction_strategy="regex", validator_rules=["non_empty"]),
                    SchemaFieldDefinition(name="act_date", required=True, extraction_strategy="date_regex", validator_rules=["date"], scoring_type="date_equivalence"),
                    SchemaFieldDefinition(name="seller_name", required=False, extraction_strategy="label_lookup", scoring_type="fuzzy_text"),
                    SchemaFieldDefinition(name="buyer_name", required=False, extraction_strategy="label_lookup", scoring_type="fuzzy_text"),
                    SchemaFieldDefinition(name="total", required=False, extraction_strategy="amount_lookup", scoring_type="numeric_tolerance"),
                    SchemaFieldDefinition(name="currency", required=False, extraction_strategy="currency_symbol_detection"),
                ],
            ),
            "contract": DocumentSchemaDefinition(
                name="contract",
                version="1.0",
                model=ContractSchema,
                instructions="Извлекай реквизиты договора и итоговую сумму при наличии.",
                fields=[
                    SchemaFieldDefinition(name="contract_number", required=True, extraction_strategy="regex", validator_rules=["non_empty"]),
                    SchemaFieldDefinition(name="contract_date", required=True, extraction_strategy="date_regex", validator_rules=["date"], scoring_type="date_equivalence"),
                    SchemaFieldDefinition(name="party_a", required=False, extraction_strategy="label_lookup", scoring_type="fuzzy_text"),
                    SchemaFieldDefinition(name="party_b", required=False, extraction_strategy="label_lookup", scoring_type="fuzzy_text"),
                    SchemaFieldDefinition(name="total_amount", required=False, extraction_strategy="amount_lookup", scoring_type="numeric_tolerance"),
                    SchemaFieldDefinition(name="currency", required=False, extraction_strategy="currency_symbol_detection"),
                ],
            ),
        }

    def get(self, document_type: str) -> DocumentSchemaDefinition:
        if document_type not in self._schemas:
            raise KeyError(f"Unsupported document type: {document_type}")
        return self._schemas[document_type]

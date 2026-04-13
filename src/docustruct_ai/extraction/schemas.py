from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SchemaFieldDefinition(BaseModel):
    name: str
    required: bool = False
    extraction_strategy: str
    validator_rules: list[str] = Field(default_factory=list)
    scoring_type: str = "exact"
    description: str | None = None


class InvoiceLineItem(BaseModel):
    description: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    total: float | None = None


class InvoiceSchema(BaseModel):
    supplier_name: str | None = None
    buyer_name: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    due_date: str | None = None
    currency: str | None = None
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    line_items: list[InvoiceLineItem] = Field(default_factory=list)


class ActSchema(BaseModel):
    act_number: str | None = None
    act_date: str | None = None
    seller_name: str | None = None
    buyer_name: str | None = None
    total: float | None = None
    currency: str | None = None


class ContractSchema(BaseModel):
    contract_number: str | None = None
    contract_date: str | None = None
    party_a: str | None = None
    party_b: str | None = None
    total_amount: float | None = None
    currency: str | None = None


class DocumentSchemaDefinition(BaseModel):
    name: str
    version: str
    model: type[BaseModel]
    fields: list[SchemaFieldDefinition]
    instructions: str

    def field_map(self) -> dict[str, SchemaFieldDefinition]:
        return {field.name: field for field in self.fields}

    def json_schema(self) -> dict[str, Any]:
        return self.model.model_json_schema()

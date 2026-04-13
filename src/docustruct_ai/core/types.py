from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


FieldRoute = Literal["accepted", "needs_review", "rejected"]


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

    def as_list(self) -> list[float]:
        return [self.x1, self.y1, self.x2, self.y2]

    @classmethod
    def from_list(cls, data: list[float]) -> "BoundingBox":
        return cls(x1=data[0], y1=data[1], x2=data[2], y2=data[3])


class Span(BaseModel):
    id: str
    page: int
    text: str
    bbox: BoundingBox
    confidence: float | None = None
    source_engine: str
    level: str = "word"
    metadata: dict[str, Any] = Field(default_factory=dict)


class Region(BaseModel):
    id: str
    page: int
    kind: str
    bbox: BoundingBox
    text: str | None = None
    reading_order: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class TableRegion(Region):
    rows: list[list[str]] = Field(default_factory=list)


class ParsedPage(BaseModel):
    page_number: int
    width: float
    height: float
    regions: list[Region] = Field(default_factory=list)
    tables: list[TableRegion] = Field(default_factory=list)
    key_value_candidates: list[Region] = Field(default_factory=list)
    reading_order: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedDocument(BaseModel):
    document_id: str
    pages: list[ParsedPage]
    metadata: dict[str, Any] = Field(default_factory=dict)


class FieldEvidence(BaseModel):
    page: int
    bbox: list[float] | None = None
    evidence_text: str
    source_engine: str
    source_region_id: str | None = None
    grounding_score: float = 0.0


class ValidationIssue(BaseModel):
    scope: Literal["field", "document"]
    field_name: str | None = None
    status: Literal["ok", "warning", "error"]
    rule_name: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ExtractionFieldResult(BaseModel):
    field_name: str
    value: Any = None
    normalized_value: Any = None
    value_type: str = "string"
    confidence: float = 0.0
    required: bool = False
    route: FieldRoute = "needs_review"
    evidence: FieldEvidence | None = None
    validation_issues: list[ValidationIssue] = Field(default_factory=list)
    alternatives: list[Any] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentResult(BaseModel):
    document_id: str
    document_type: str
    schema_name: str
    payload: dict[str, Any]
    fields: list[ExtractionFieldResult]
    validation_issues: list[ValidationIssue]
    confidence: float
    route: FieldRoute
    routing_reasons: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

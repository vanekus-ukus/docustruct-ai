from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from docustruct_ai.db.base import Base


class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    schema_name: Mapped[str] = mapped_column(String(128))
    schema_version: Mapped[str] = mapped_column(String(32), default="1.0")
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["Document"] = relationship("Document", back_populates="entities")
    fields: Mapped[list["ExtractedField"]] = relationship(
        "ExtractedField", back_populates="entity", cascade="all, delete"
    )


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(Integer, ForeignKey("extracted_entities.id"), index=True)
    field_name: Mapped[str] = mapped_column(String(128), index=True)
    value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_value: Mapped[dict | str | list | None] = mapped_column(JSON, nullable=True)
    value_type: Mapped[str] = mapped_column(String(64), default="string")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    routing_state: Mapped[str] = mapped_column(String(64), default="needs_review", index=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    entity: Mapped["ExtractedEntity"] = relationship("ExtractedEntity", back_populates="fields")
    evidence_items: Mapped[list["FieldEvidenceModel"]] = relationship(
        "FieldEvidenceModel", back_populates="field", cascade="all, delete"
    )
    validation_reports: Mapped[list["ValidationReport"]] = relationship(
        "ValidationReport", back_populates="field", cascade="all, delete"
    )
    review_tasks: Mapped[list["ReviewTask"]] = relationship(
        "ReviewTask", back_populates="field", cascade="all, delete"
    )


class FieldEvidenceModel(Base):
    __tablename__ = "field_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    field_id: Mapped[int] = mapped_column(Integer, ForeignKey("extracted_fields.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    bbox_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    evidence_text: Mapped[str] = mapped_column(Text)
    source_engine: Mapped[str] = mapped_column(String(255))
    source_region_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    grounding_score: Mapped[float] = mapped_column(Float, default=0.0)

    field: Mapped["ExtractedField"] = relationship("ExtractedField", back_populates="evidence_items")


class ValidationReport(Base):
    __tablename__ = "validation_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    field_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("extracted_fields.id"), nullable=True, index=True
    )
    scope: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), index=True)
    rule_name: Mapped[str] = mapped_column(String(128))
    message: Mapped[str] = mapped_column(Text)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)

    document: Mapped["Document"] = relationship("Document", back_populates="validation_reports")
    field: Mapped["ExtractedField"] = relationship("ExtractedField", back_populates="validation_reports")

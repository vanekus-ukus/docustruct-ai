from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from docustruct_ai.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_type: Mapped[str] = mapped_column(String(64), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(255))
    source_path: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="uploaded", index=True)
    routing_state: Mapped[str] = mapped_column(String(64), default="needs_review", index=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    pages: Mapped[list["Page"]] = relationship("Page", back_populates="document", cascade="all, delete")
    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="document", cascade="all, delete")
    engine_runs: Mapped[list["EngineRun"]] = relationship(
        "EngineRun", back_populates="document", cascade="all, delete"
    )
    parsed_regions: Mapped[list["ParsedRegion"]] = relationship(
        "ParsedRegion", back_populates="document", cascade="all, delete"
    )
    ocr_spans: Mapped[list["OCRSpan"]] = relationship(
        "OCRSpan", back_populates="document", cascade="all, delete"
    )
    entities: Mapped[list["ExtractedEntity"]] = relationship(
        "ExtractedEntity", back_populates="document", cascade="all, delete"
    )
    validation_reports: Mapped[list["ValidationReport"]] = relationship(
        "ValidationReport", back_populates="document", cascade="all, delete"
    )
    review_tasks: Mapped[list["ReviewTask"]] = relationship(
        "ReviewTask", back_populates="document", cascade="all, delete"
    )


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    width: Mapped[float] = mapped_column(Float)
    height: Mapped[float] = mapped_column(Float)
    rotation: Mapped[int] = mapped_column(Integer, default=0)
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    document: Mapped["Document"] = relationship("Document", back_populates="pages")
    parsed_regions: Mapped[list["ParsedRegion"]] = relationship(
        "ParsedRegion", back_populates="page", cascade="all, delete"
    )
    ocr_spans: Mapped[list["OCRSpan"]] = relationship("OCRSpan", back_populates="page", cascade="all, delete")

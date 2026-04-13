from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from docustruct_ai.db.base import Base


class EngineRun(Base):
    __tablename__ = "engine_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    job_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=True)
    engine_type: Mapped[str] = mapped_column(String(64), index=True)
    engine_name: Mapped[str] = mapped_column(String(255))
    engine_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(64), default="ok")
    input_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    output_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["Document"] = relationship("Document", back_populates="engine_runs")
    job: Mapped["Job"] = relationship("Job", back_populates="engine_runs")


class ParsedRegion(Base):
    __tablename__ = "parsed_regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    page_id: Mapped[int] = mapped_column(Integer, ForeignKey("pages.id"), index=True)
    region_type: Mapped[str] = mapped_column(String(64), index=True)
    bbox_json: Mapped[list] = mapped_column(JSON)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reading_order: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    document: Mapped["Document"] = relationship("Document", back_populates="parsed_regions")
    page: Mapped["Page"] = relationship("Page", back_populates="parsed_regions")


class OCRSpan(Base):
    __tablename__ = "ocr_spans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    page_id: Mapped[int] = mapped_column(Integer, ForeignKey("pages.id"), index=True)
    span_type: Mapped[str] = mapped_column(String(32), default="word")
    text: Mapped[str] = mapped_column(Text)
    bbox_json: Mapped[list] = mapped_column(JSON)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_engine: Mapped[str] = mapped_column(String(255))
    reading_order: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    document: Mapped["Document"] = relationship("Document", back_populates="ocr_spans")
    page: Mapped["Page"] = relationship("Page", back_populates="ocr_spans")

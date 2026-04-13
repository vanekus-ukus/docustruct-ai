from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from docustruct_ai.db.base import Base


class ReviewTask(Base):
    __tablename__ = "review_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), index=True)
    field_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("extracted_fields.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    reason: Mapped[str] = mapped_column(Text)
    candidate_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="review_tasks")
    field: Mapped["ExtractedField"] = relationship("ExtractedField", back_populates="review_tasks")
    decisions: Mapped[list["ReviewDecision"]] = relationship(
        "ReviewDecision", back_populates="review_task", cascade="all, delete"
    )


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_task_id: Mapped[int] = mapped_column(Integer, ForeignKey("review_tasks.id"), index=True)
    decision: Mapped[str] = mapped_column(String(32))
    final_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    review_task: Mapped["ReviewTask"] = relationship("ReviewTask", back_populates="decisions")

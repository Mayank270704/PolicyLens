from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class Comment(Base, TimestampMixin):
    """A public comment. `original_text` is immutable -- never updated
    after insert (requirement: "Preserve original comment text"); any
    processed/normalized form lives in a separate column, never in place
    of it, per this project's standing immutability principle."""

    __tablename__ = "comments"
    __table_args__ = (UniqueConstraint("policy_document_id", "normalized_text_hash", name="uq_comment_dedup"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    policy_document_id: Mapped[int] = mapped_column(ForeignKey("policy_documents.id"), nullable=False)
    policy_section_id: Mapped[Optional[int]] = mapped_column(ForeignKey("policy_sections.id"), nullable=True)

    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    # SHA-256 of normalized_text, used for the dedup unique constraint above --
    # keeps the index small and avoids a huge-text unique index.
    normalized_text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    language: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    multiplicity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    validation_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    pii_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    redacted_text_for_display: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_metadata: Mapped[Optional["CommentSourceMetadata"]] = relationship(
        back_populates="comment", uselist=False, cascade="all, delete-orphan"
    )
    stance_predictions: Mapped[list["StancePrediction"]] = relationship(
        back_populates="comment", cascade="all, delete-orphan"
    )


class CommentSourceMetadata(Base, TimestampMixin):
    """Where a comment came from (requirement: "Comment source
    metadata" as its own entity, "Preserve source IDs"). One-to-one with
    Comment, kept separate so Comment itself stays focused on the text
    and its direct annotations."""

    __tablename__ = "comment_source_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), unique=True, nullable=False)

    source_dataset: Mapped[str] = mapped_column(String(200), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(200), nullable=False)
    collection_channel: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    submitted_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    comment: Mapped["Comment"] = relationship(back_populates="source_metadata")

from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, str_enum
from backend.app.models.enums import SummaryMethod


class Summary(Base, TimestampMixin):
    """A per-concern-group summary. Defaults to extractive (see
    docs/architecture/SYSTEM_ARCHITECTURE.md component 9's scope note);
    abstractive summaries are supported by the schema but require
    model_version_id, enforced at the application layer in
    services/validation.py since a portable CheckConstraint referencing
    an EvidenceReference COUNT isn't expressible in plain SQL without a
    trigger."""

    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("concern_groups.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[SummaryMethod] = mapped_column(str_enum(SummaryMethod), nullable=False, default=SummaryMethod.EXTRACTIVE)
    model_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("model_versions.id"), nullable=True)

    evidence_references: Mapped[list["EvidenceReference"]] = relationship(
        back_populates="summary", cascade="all, delete-orphan", order_by="EvidenceReference.rank"
    )


class EvidenceReference(Base, TimestampMixin):
    """Links a Summary to the comment(s) that support it. A Summary with
    zero EvidenceReference rows is an invalid record per
    docs/architecture/DATA_MODEL.md's traceability guarantees -- enforced
    at creation time in services, and checked after the fact by the
    traceability integrity check (see
    backend/app/services/validation.py and
    research/methodology/RESEARCH_QUESTIONS_AND_HYPOTHESES.md RQ4)."""

    __tablename__ = "evidence_references"
    __table_args__ = (UniqueConstraint("summary_id", "comment_id", name="uq_evidence_once_per_summary"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    summary_id: Mapped[int] = mapped_column(ForeignKey("summaries.id"), nullable=False)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    summary: Mapped["Summary"] = relationship(back_populates="evidence_references")

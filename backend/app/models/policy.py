from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, str_enum
from backend.app.models.enums import DocumentProcessingStatus


class PolicyDocument(Base, TimestampMixin):
    """A policy a comment campaign is collected against. Supports
    multiple policies (requirement: "Support multiple policies") -- every
    Comment/ConcernGroup/PolicyReport references a specific policy_id."""

    __tablename__ = "policy_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    sections: Mapped[list["PolicySection"]] = relationship(
        back_populates="policy_document", cascade="all, delete-orphan"
    )
    versions: Mapped[list["PolicyDocumentVersion"]] = relationship(
        back_populates="policy_document", cascade="all, delete-orphan", order_by="PolicyDocumentVersion.version_number"
    )


class PolicyDocumentVersion(Base, TimestampMixin):
    """Append-only versioning (requirement: "Document versioning", "Do not
    overwrite original uploaded documents"). Each re-upload/reprocessing
    of a policy document creates a NEW row here; raw_text is immutable
    once written -- never updated in place."""

    __tablename__ = "policy_document_versions"
    __table_args__ = (UniqueConstraint("policy_document_id", "version_number", name="uq_policy_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    policy_document_id: Mapped[int] = mapped_column(ForeignKey("policy_documents.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_format: Mapped[str] = mapped_column(String(20), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DocumentProcessingStatus] = mapped_column(
        str_enum(DocumentProcessingStatus), default=DocumentProcessingStatus.PENDING, nullable=False
    )
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    policy_document: Mapped["PolicyDocument"] = relationship(back_populates="versions")


class PolicySection(Base, TimestampMixin):
    """A section/clause identified within one specific document VERSION,
    or -- when no section structure could be identified -- a single row
    representing the whole document (see docs/architecture/DATA_MODEL.md's
    accommodation for real corpora with no formal clause structure).

    Scoped to a version (not just the policy document) because
    re-ingesting a document creates a new version with its own freshly
    identified sections, never overwriting or colliding with a prior
    version's -- consistent with this project's append-only versioning
    principle."""

    __tablename__ = "policy_sections"
    __table_args__ = (
        UniqueConstraint("policy_document_version_id", "section_label", name="uq_policy_section_label"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    policy_document_id: Mapped[int] = mapped_column(ForeignKey("policy_documents.id"), nullable=False)
    policy_document_version_id: Mapped[int] = mapped_column(
        ForeignKey("policy_document_versions.id"), nullable=False
    )
    section_label: Mapped[str] = mapped_column(String(300), nullable=False)
    section_text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(nullable=False, default=0)

    policy_document: Mapped["PolicyDocument"] = relationship(back_populates="sections")

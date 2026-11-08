from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin


class ConcernGroup(Base, TimestampMixin):
    """A cluster of comments sharing an underlying concern -- produced
    independent of stance (docs/architecture/SYSTEM_ARCHITECTURE.md's
    design principle). Nothing on this model, or on GroupMembership
    below, references StancePrediction or label/exclusion_code -- that
    independence is enforced by simply never having a column for it, not
    by a convention someone could accidentally violate."""

    __tablename__ = "concern_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    policy_document_id: Mapped[int] = mapped_column(ForeignKey("policy_documents.id"), nullable=False)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"), nullable=False)

    method: Mapped[str] = mapped_column(String(20), nullable=False)  # "hdbscan" | "kmeans"
    hyperparameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_noise: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    memberships: Mapped[list["GroupMembership"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    representative_comments: Mapped[list["RepresentativeComment"]] = relationship(
        back_populates="group", cascade="all, delete-orphan", order_by="RepresentativeComment.rank"
    )


class GroupMembership(Base, TimestampMixin):
    """comment_id -> group_id. A comment belongs to at most one group per
    clustering run (baseline design, per SEMANTIC_GROUPING_EXPERIMENT_PLAN.md);
    HDBSCAN noise is represented by `ConcernGroup.is_noise=True`, never by
    omitting the comment (requirement: "Do not force every comment into a
    cluster. Allow unassigned or noise comments" -- noise comments still
    get a membership row, into a group explicitly marked as noise, so
    they remain queryable rather than silently dropped)."""

    __tablename__ = "group_memberships"
    __table_args__ = (
        UniqueConstraint("comment_id", "model_version_id", name="uq_one_group_per_comment_per_run"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("concern_groups.id"), nullable=False)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"), nullable=False)

    group: Mapped["ConcernGroup"] = relationship(back_populates="memberships")


class RepresentativeComment(Base, TimestampMixin):
    """A comment selected to represent a group (3-5 per group typically).
    Multiple representative comments per group are expected -- never just
    one cherry-picked example (SEMANTIC_GROUPING_EXPERIMENT_PLAN.md)."""

    __tablename__ = "representative_comments"
    __table_args__ = (UniqueConstraint("group_id", "comment_id", name="uq_representative_once_per_group"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("concern_groups.id"), nullable=False)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    group: Mapped["ConcernGroup"] = relationship(back_populates="representative_comments")

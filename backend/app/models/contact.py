from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin


class SubmitterContact(Base, TimestampMixin):
    """Contact details, kept in a table DELIBERATELY SEPARATE from
    `comments` and every research/export/analytics path (requirement:
    "Separation of contact details from research records").

    No code in `services/bulk_export.py`, `services/analytics.py`,
    `services/retrieval.py`, or `scripts/annotation/`'s CSV schema
    references this table, by construction -- a research export built
    from `Comment`/`StancePrediction`/`ConcernGroup` structurally cannot
    leak a contact field that was never selected or joined. This table
    is not yet populated by any endpoint (no live submission form collects
    contact info in this phase); it exists as the schema-level contract
    for where that information WOULD go if a future form adds it, so that
    "where does contact info live" is answered before it's ever needed,
    not improvised later under time pressure.

    One-to-one with Comment, nullable fields: a comment can exist with no
    contact record at all, which is the expected common case for most
    collection channels (e.g. historical datasets with no submitter
    contact info available at all)."""

    __tablename__ = "submitter_contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), unique=True, nullable=False)

    email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    consent_to_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

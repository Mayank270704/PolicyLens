from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TypeVar

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


_E = TypeVar("_E", bound=enum.Enum)


def str_enum(enum_cls: type[_E]) -> SAEnum:
    """A SQLAlchemy Enum type that stores the member's *value* (e.g.
    "Support") rather than SQLAlchemy's default of the member's *name*
    (e.g. "SUPPORT") -- so the database's stored strings exactly match
    scripts/annotation/schema.py's STANCE_LABELS/EXCLUSION_CODES
    conventions, and so raw-SQL CheckConstraints comparing against a
    literal string (e.g. "source = 'human'") compare against what's
    actually stored.

    `native_enum=False` is deliberate, not an oversight: SQLAlchemy's
    default on PostgreSQL is to create a native `CREATE TYPE ... AS ENUM`
    type, while on SQLite the same column is just VARCHAR + a CHECK
    constraint -- confirmed by compiling this project's own DDL against
    both dialects (see docs/backend/DATABASE_COMPATIBILITY.md). A native
    PG enum type requires `ALTER TYPE ... ADD VALUE` (which historically
    couldn't even run inside a transaction) to ever add a new member,
    versus a plain column-constraint change on SQLite -- a real behavioral
    and migration-complexity divergence this project avoids entirely by
    forcing both dialects to the same VARCHAR + CHECK representation,
    rather than silently letting Postgres behave differently."""
    return SAEnum(enum_cls, values_callable=lambda obj: [e.value for e in obj], native_enum=False)

"""SQLAlchemy engine/session setup. SQLite by default (zero external
service dependency, CPU-only, free) -- swappable to PostgreSQL later via
DATABASE_URL, per docs/architecture/DATA_MODEL.md's proposed migration
path, without any model code changes (SQLAlchemy abstracts the dialect).
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.models.base import Base

_settings = get_settings()

_connect_args = {"check_same_thread": False} if _settings.database_url.startswith("sqlite") else {}
engine = create_engine(_settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Creates all tables if they don't exist. No migration system is
    wired up yet (Alembic is installed and available for a future
    phase) -- see docs/backend/DEVELOPER_GUIDE.md."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

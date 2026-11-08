import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def db_session():
    """An isolated, in-memory SQLite database per test -- never the real
    default backend/policylens_dev.db file, and never
    data/annotations/ -- so backend tests cannot collide with each other,
    with a developer's local dev database, or with the annotation
    subsystem's own files."""
    from backend.app.models.base import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session):
    """A FastAPI TestClient wired to the isolated db_session above via
    dependency override -- the app's own lifespan/init_db (which would
    touch the real default database file) is never triggered, since this
    fixture does not enter TestClient as a context manager."""
    from fastapi.testclient import TestClient

    from backend.app.database import get_db
    from backend.app.main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()

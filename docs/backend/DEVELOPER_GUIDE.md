# Backend Developer Guide

## Layout

```
backend/app/
  config.py           # Settings from environment variables, no hardcoded secrets
  database.py         # SQLAlchemy engine/session, init_db()
  main.py             # FastAPI app, lifespan, exception handlers, router registration
  models/             # SQLAlchemy ORM models -- see docs/backend/DATABASE_SCHEMA.md
  schemas/             # Pydantic request/response schemas
  services/
    pagination.py      # Shared LIMIT/OFFSET pagination helper
    privacy.py          # PII-flagging heuristic (not a certified anonymizer)
    validation.py        # Text normalization, exclusion-code heuristic, traceability integrity check
  ml_interfaces/        # Abstract ML contracts -- see docs/backend/ML_INTEGRATION_GUIDE.md
  documents/             # Policy-document ingestion: extraction.py, sections.py, ingestion.py
  routers/                # FastAPI endpoint definitions, one file per resource group
```

## Running tests

```
python -m pytest tests/
```

Backend tests (`tests/unit/test_backend_models.py`,
`test_ml_interfaces.py`, `test_document_ingestion.py`,
`test_privacy_and_validation.py`, `tests/integration/test_backend_api.py`)
use the `db_session`/`client` fixtures in `tests/conftest.py`: an
**in-memory SQLite database per test**, with the app's `get_db`
dependency overridden. These tests never touch the real default database
file (`backend/policylens_dev.db`) and never trigger the app's
`lifespan`/`init_db` against it. Every fixture in every backend test is
synthetic, constructed in the test itself — none of this reads from or
writes to `data/annotations/`.

## Security and privacy

- **File upload validation**: extension allowlist + size cap, checked
  *before* any file content is read into an extractor
  (`documents/ingestion.py::validate_upload`).
- **Request validation**: Pydantic schemas reject blank/oversized/
  malformed input before it reaches any handler logic.
- **Secure configuration handling**: no secret or credential is
  hardcoded anywhere in `backend/`; everything configurable comes from
  environment variables with safe defaults (`config.py`).
- **Access control interfaces**: not implemented yet (no authentication
  system exists in this phase) — every endpoint is currently open. This
  is a known gap for any real deployment and is listed under Limitations
  below, not glossed over.
- **PII detection integration point**: `services/privacy.py::scan_for_pii`.
  **This is a regex heuristic, not a certified anonymization system** —
  its own `PiiScanResult.DISCLAIMER` states explicitly that a clean scan
  does not mean the text is anonymous. Comment validation
  (`POST /comments/{id}/validate`) surfaces this flag for human review;
  nothing in this backend treats it as a guarantee.
- **Logging**: comment text is never logged by default
  (`LOG_COMMENT_TEXT=false` in `.env.example`) — an operator must
  explicitly opt in, and even then it's intended for local debugging
  only, never a default-on behavior.

## Known limitations

- **Role-based authorization is an interface, not a real auth system.**
  `services/authz.py` is wired onto the 3 endpoints exposing raw/bulk
  data, but `get_current_user()` defaults every request to admin — there
  is no login or token verification yet. See
  `docs/backend/PRIVACY_AND_ACCESS_CONTROL.md` for exactly which
  endpoints are gated and which aren't.
- **PII detection is a narrow heuristic** (email/phone/SSN-shaped
  patterns only) — see `services/privacy.py`'s own docstring. It will
  miss names, locations, and other re-identifying but unstructured
  content.
- **Section identification is a heuristic**, not a robust document
  parser (`documents/sections.py`) — real policy documents vary too much
  in structure for a general solution; it falls back to a single
  whole-document section when it finds nothing more specific.
- **No migrations system wired up.** Alembic is installed and available;
  `init_db()` currently creates tables directly via
  `Base.metadata.create_all()`. Fine for early development, not for a
  schema that needs to evolve under real data without data loss — set up
  Alembic before that becomes a real constraint.
- **No ML component is implemented** — every prediction/clustering/
  abstractive-summarization interface raises `MLComponentNotImplemented`
  by design (see `ML_INTEGRATION_GUIDE.md`). This is not a bug to fix; it
  correctly reflects that no model has been trained yet.

## Relationship to other parts of this project

- **`scripts/annotation/`** — the single-annotator CSV-based research
  tool. Separate storage, separate purpose. Shares only
  `ml.stance_classification.dataset_prep.normalize_text` with this
  backend (one normalization implementation, reused rather than
  duplicated).
- **`ml/stance_classification/`** — dataset preparation for training a
  real classifier. This backend's `ml_interfaces.StanceClassifier` is
  the contract a model trained via that pipeline would eventually
  implement.
- **`docs/architecture/`** — the design this backend implements a subset
  of. `SYSTEM_ARCHITECTURE.md` and `DATA_MODEL.md` describe components
  (clustering, summarization, backend, database, frontend) at a design
  level; this backend phase made the database and API real, and the ML
  components explicit-but-not-yet-implemented contracts.

"""Backend configuration, read from environment variables (see .env.example).

No secrets are hardcoded here. No paid external API is referenced
anywhere in this configuration -- every setting is for local, free,
CPU-only operation.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Default: a local SQLite file, deliberately kept OUTSIDE data/annotations/
# (and outside data/ entirely) so there is no risk of path confusion with
# the single-annotator research tooling in scripts/annotation/.
DEFAULT_DATABASE_PATH = REPO_ROOT / "backend" / "policylens_dev.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"

MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB; generous for a policy document, bounded to avoid memory spikes
SUPPORTED_DOCUMENT_EXTENSIONS = (".txt", ".html", ".htm", ".pdf")

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 200


class Settings:
    def __init__(self) -> None:
        self.app_env: str = os.environ.get("APP_ENV", "development")
        self.database_url: str = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
        self.max_upload_size_bytes: int = int(
            os.environ.get("MAX_UPLOAD_SIZE_BYTES", MAX_UPLOAD_SIZE_BYTES)
        )
        self.log_comment_text: bool = os.environ.get("LOG_COMMENT_TEXT", "false").lower() == "true"
        retention_raw = os.environ.get("RETENTION_POLICY_DAYS", "")
        self.retention_policy_days: int | None = int(retention_raw) if retention_raw.strip() else None
        # None (the default) means indefinite retention -- an explicit choice for a
        # research project, not an oversight. Set a positive integer to enable the
        # retention-candidate report in services/retention.py. See
        # docs/backend/PRIVACY_AND_ACCESS_CONTROL.md.
        # Deliberately defaults to False -- see docs/backend/DEVELOPER_GUIDE.md's
        # privacy/logging section. Comment text is never logged unless this is
        # explicitly opted into (e.g. for local debugging), and even then it is
        # the operator's deliberate choice, not the default.


def get_settings() -> Settings:
    return Settings()

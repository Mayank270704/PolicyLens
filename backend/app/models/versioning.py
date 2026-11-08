from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin, str_enum
from backend.app.models.enums import ModelComponent


class ModelVersion(Base, TimestampMixin):
    """Identifies a specific trained/configured ML component version --
    referenced by StancePrediction (source=model), ConcernGroup, and
    Summary (method=abstractive), so every machine-generated record says
    exactly which model/config produced it (requirement: "Preserve
    historical processing versions"). Rows here are never deleted or
    edited once referenced -- a new version is a new row."""

    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    component: Mapped[ModelComponent] = mapped_column(str_enum(ModelComponent), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version_string: Mapped[str] = mapped_column(String(100), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source_data_hash: Mapped[str] = mapped_column(String(64), nullable=True)

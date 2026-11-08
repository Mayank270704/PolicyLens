from __future__ import annotations

from typing import Optional

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, str_enum
from backend.app.models.enums import ExclusionCode, PredictionSource, StanceLabel


class StancePrediction(Base, TimestampMixin):
    """A stance decision for one comment -- human-annotated or
    model-predicted, explicitly distinguished via `source`
    (docs/architecture/DATA_MODEL.md's StanceAnnotation design).
    Kept independent of ConcernGroup: nothing here references a group,
    and nothing in concern.py references a label (requirement: "Keep
    individual stance predictions independent of concern groups")."""

    __tablename__ = "stance_predictions"
    __table_args__ = (
        CheckConstraint(
            "NOT (label IS NOT NULL AND exclusion_code IS NOT NULL)",
            name="ck_stance_label_xor_exclusion",
        ),
        CheckConstraint(
            "(source = 'human') OR (source = 'model' AND model_version_id IS NOT NULL)",
            name="ck_model_prediction_has_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"), nullable=False)

    label: Mapped[Optional[StanceLabel]] = mapped_column(str_enum(StanceLabel), nullable=True)
    exclusion_code: Mapped[Optional[ExclusionCode]] = mapped_column(str_enum(ExclusionCode), nullable=True)
    confidence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source: Mapped[PredictionSource] = mapped_column(str_enum(PredictionSource), nullable=False)
    annotator_or_model_ref: Mapped[str] = mapped_column(String(200), nullable=False)
    model_version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("model_versions.id"), nullable=True)
    pass_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    comment: Mapped["Comment"] = relationship(back_populates="stance_predictions")  # noqa: F821
    model_version: Mapped[Optional["ModelVersion"]] = relationship()  # noqa: F821

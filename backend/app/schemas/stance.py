from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class StancePredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    comment_id: int
    label: Optional[str]
    exclusion_code: Optional[str]
    confidence: Optional[int]
    notes: Optional[str]
    source: str
    annotator_or_model_ref: str
    model_version_id: Optional[int]
    pass_number: int
    created_at: datetime

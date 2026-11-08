from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PolicyReportOut(BaseModel):
    policy_document_id: int
    generated_at: datetime
    total_comments: int
    stance_distribution: dict[str, int]
    exclusion_distribution: dict[str, int]
    pending_count: int
    concern_group_count: int
    noise_comment_count: int
    completeness_flags: dict[str, bool]

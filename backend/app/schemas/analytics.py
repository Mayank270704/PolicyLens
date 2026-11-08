from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PolicyAnalyticsOut(BaseModel):
    policy_document_id: int
    total_comments: int
    comments_by_source: dict[str, int]
    language_distribution: dict[str, int]
    submission_timeline: dict[str, int]
    data_quality: dict[str, int | float]
    stance_available: bool
    stance_distribution: dict[str, int]
    exclusion_distribution: dict[str, int]
    pending_stance_count: int
    concern_groups_available: bool
    concern_group_count: int
    noise_comment_count: int
    generated_at: datetime


class CrossPolicySummaryOut(BaseModel):
    total_comments: int
    comments_by_policy: dict[str, int]
    total_policies: int

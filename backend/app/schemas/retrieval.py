from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RetrievalResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_id: int
    section_label: str
    score: float
    snippet: str
    policy_document_id: int
    policy_document_version_id: int
    method: str
    query: str
    retrieved_at: datetime


class RetrievalResponse(BaseModel):
    results: list[RetrievalResultOut]
    accuracy_disclaimer: str = (
        "No retrieval accuracy (precision/recall) is claimed -- there is no labeled "
        "relevance-evaluation dataset for this corpus. Scores are raw BM25 relevance "
        "scores, not calibrated probabilities or accuracy figures."
    )

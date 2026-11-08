from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ClusterAssignment:
    comment_id: int
    group_label: int  # -1 reserved for noise, matching HDBSCAN's own convention
    is_noise: bool


class ConcernGrouper(ABC):
    """Contract for docs/experiments/SEMANTIC_GROUPING_EXPERIMENT_PLAN.md.
    Takes embeddings ONLY -- deliberately no stance-label parameter
    anywhere in this signature, enforcing the independence principle at
    the interface level, not just by convention."""

    @abstractmethod
    def fit_predict(self, comment_ids: list[int], embeddings: list[list[float]]) -> list[ClusterAssignment]: ...

    @property
    @abstractmethod
    def method_name(self) -> str: ...  # "hdbscan" | "kmeans"


class NotYetConfiguredConcernGrouper(ConcernGrouper):
    def fit_predict(self, comment_ids: list[int], embeddings: list[list[float]]) -> list[ClusterAssignment]:
        from backend.app.ml_interfaces.base import MLComponentNotImplemented

        raise MLComponentNotImplemented(
            "No concern-grouping implementation is configured -- see "
            "docs/experiments/SEMANTIC_GROUPING_EXPERIMENT_PLAN.md."
        )

    @property
    def method_name(self) -> str:
        return "unconfigured"

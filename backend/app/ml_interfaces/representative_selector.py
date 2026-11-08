from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RepresentativeSelection:
    comment_id: int
    rank: int
    similarity_score: float


class RepresentativeSelector(ABC):
    """Contract for selecting 3-5 representative comments per concern
    group (docs/architecture/SYSTEM_ARCHITECTURE.md component 8)."""

    @abstractmethod
    def select(
        self, group_comment_ids: list[int], embeddings: dict[int, list[float]], top_n: int = 5
    ) -> list[RepresentativeSelection]: ...


class CentroidSimilarityRepresentativeSelector(RepresentativeSelector):
    """A real, simple, CPU-only implementation: ranks group members by
    cosine similarity to the group's own centroid. This one IS
    implemented (not a NotImplemented stub) because it needs no trained
    model, no download, and no fabricated prediction -- just arithmetic
    over embeddings the caller already has."""

    def select(
        self, group_comment_ids: list[int], embeddings: dict[int, list[float]], top_n: int = 5
    ) -> list[RepresentativeSelection]:
        if not group_comment_ids:
            return []

        import math

        vectors = [embeddings[cid] for cid in group_comment_ids]
        dim = len(vectors[0])
        centroid = [sum(v[i] for v in vectors) / len(vectors) for i in range(dim)]

        def cosine(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(y * y for y in b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)

        scored = [
            (cid, cosine(embeddings[cid], centroid))
            for cid in group_comment_ids
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)

        n = min(top_n, len(scored))
        return [
            RepresentativeSelection(comment_id=cid, rank=i + 1, similarity_score=score)
            for i, (cid, score) in enumerate(scored[:n])
        ]

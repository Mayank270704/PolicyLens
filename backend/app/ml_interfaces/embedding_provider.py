from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Contract for turning normalized_text into dense vectors, shared by
    stance-classification experiment 3 and the semantic-grouping plan
    (docs/experiments/*_EXPERIMENT_PLAN.md both specify
    sentence-transformers/all-MiniLM-L6-v2 as the default model, reused
    across both rather than loaded twice -- see
    docs/experiments/HARDWARE_FEASIBILITY_REPORT.md's "load one large
    model at a time" practice)."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def dimension(self) -> int: ...


class NotYetConfiguredEmbeddingProvider(EmbeddingProvider):
    """No embedding model is loaded by default -- loading one (even a
    small, CPU-friendly one) triggers a one-time download from the
    Hugging Face Hub on first use, which this interface never does
    implicitly. A real implementation is wired in explicitly when an
    experiment from the plan actually runs."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        from backend.app.ml_interfaces.base import MLComponentNotImplemented

        raise MLComponentNotImplemented(
            "No embedding provider is configured. Wire in a concrete implementation "
            "(e.g. sentence-transformers/all-MiniLM-L6-v2) explicitly before use -- "
            "never implicitly, since loading a model may trigger a download."
        )

    @property
    def model_name(self) -> str:
        return "unconfigured"

    @property
    def dimension(self) -> int:
        return 0

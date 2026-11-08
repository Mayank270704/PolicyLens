"""Abstract ML integration interfaces (Phase 5).

Each interface below is a contract the backend calls against; no concrete
implementation here produces a real prediction -- every placeholder
raises NotImplementedError explicitly rather than returning a fabricated
or hardcoded result. This lets the API, database, and tests be built and
exercised NOW (against a documented NotImplemented stub, or a test double
in tests/), with real ML components implemented later (per
docs/experiments/STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md /
SEMANTIC_GROUPING_EXPERIMENT_PLAN.md) and wired in via dependency
injection, without any surrounding code changing.
"""
from backend.app.ml_interfaces.base import MLComponentNotImplemented
from backend.app.ml_interfaces.concern_grouping import ClusterAssignment, ConcernGrouper
from backend.app.ml_interfaces.embedding_provider import EmbeddingProvider
from backend.app.ml_interfaces.representative_selector import RepresentativeSelector
from backend.app.ml_interfaces.stance_classifier import StanceClassifier, StancePredictionResult
from backend.app.ml_interfaces.summarizer import Summarizer, SummaryResult

__all__ = [
    "MLComponentNotImplemented",
    "StanceClassifier",
    "StancePredictionResult",
    "EmbeddingProvider",
    "ConcernGrouper",
    "ClusterAssignment",
    "RepresentativeSelector",
    "Summarizer",
    "SummaryResult",
]

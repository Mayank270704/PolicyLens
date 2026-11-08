from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StancePredictionResult:
    label: str | None  # one of StanceLabel.value, or None if exclusion_code is set
    exclusion_code: str | None
    confidence: float
    model_version_string: str


class StanceClassifier(ABC):
    """Contract for Experiments 1-4 in
    docs/experiments/STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md. A concrete
    implementation wraps one trained model (TF-IDF+LogReg, SBERT+linear,
    etc.) behind this interface so routers/services never need to know
    which one is active -- swap via dependency injection."""

    @abstractmethod
    def predict(self, comment_text: str, policy_context: str, policy_section: str) -> StancePredictionResult: ...

    @abstractmethod
    def predict_batch(
        self, items: list[tuple[str, str, str]]
    ) -> list[StancePredictionResult]: ...


class NotYetTrainedStanceClassifier(StanceClassifier):
    """The only implementation present today. Raises explicitly --
    does not fabricate a prediction. Per the project's own constraint
    ("Do not fabricate model predictions"), this is the correct default
    until a real classifier from the experiment plan is trained and
    validated against a finalized, non-provisional dataset."""

    def predict(self, comment_text: str, policy_context: str, policy_section: str) -> StancePredictionResult:
        from backend.app.ml_interfaces.base import MLComponentNotImplemented

        raise MLComponentNotImplemented(
            "No stance classifier has been trained yet -- see "
            "docs/experiments/STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md. "
            "Human annotation (scripts/annotation/) is the only source of stance labels right now."
        )

    def predict_batch(self, items: list[tuple[str, str, str]]) -> list[StancePredictionResult]:
        return [self.predict(*item) for item in items]

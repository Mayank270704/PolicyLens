"""Shared enums. Stance labels and exclusion codes mirror
scripts/annotation/schema.py's STANCE_LABELS / EXCLUSION_CODES exactly --
same four-class taxonomy, same four exclusion reasons, one source of
truth in spirit even though the CSV tooling and this database are
separate systems (see backend/app/__init__.py)."""
import enum


class StanceLabel(str, enum.Enum):
    SUPPORT = "Support"
    OPPOSE = "Oppose"
    NEUTRAL = "Neutral"
    UNCLEAR = "Unclear"


class ExclusionCode(str, enum.Enum):
    SPAM = "SPAM"
    OFF_TOPIC = "OFF_TOPIC"
    TOO_SHORT_NONSUBSTANTIVE = "TOO_SHORT_NONSUBSTANTIVE"
    UNINTELLIGIBLE = "UNINTELLIGIBLE"


class PredictionSource(str, enum.Enum):
    HUMAN = "human"
    MODEL = "model"


class ModelComponent(str, enum.Enum):
    STANCE_CLASSIFIER = "stance_classifier"
    EMBEDDING = "embedding"
    CLUSTERING = "clustering"
    SUMMARIZER = "summarizer"


class SummaryMethod(str, enum.Enum):
    EXTRACTIVE = "extractive"
    ABSTRACTIVE = "abstractive"


class DocumentProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"

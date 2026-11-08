from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SummaryResult:
    text: str
    method: str  # "extractive" | "abstractive"
    evidence_comment_ids: list[int]
    model_version_string: str | None = None


class Summarizer(ABC):
    @abstractmethod
    def summarize(self, representative_comment_texts: dict[int, str]) -> SummaryResult: ...


class ExtractiveSummarizer(Summarizer):
    """The current, implemented default (docs/architecture/SYSTEM_ARCHITECTURE.md
    component 9's scope note: extractive-first, abstractive explicitly
    deferred). Assembles the representative comments themselves, verbatim,
    as the "summary" -- 100% evidence coverage by construction, since the
    summary IS its own evidence."""

    def summarize(self, representative_comment_texts: dict[int, str]) -> SummaryResult:
        ordered_ids = list(representative_comment_texts.keys())
        text = "\n\n".join(f"- {representative_comment_texts[cid]}" for cid in ordered_ids)
        return SummaryResult(text=text, method="extractive", evidence_comment_ids=ordered_ids, model_version_string=None)


class NotYetConfiguredAbstractiveSummarizer(Summarizer):
    """Deliberately not implemented. Per
    research/research_gaps/RESEARCH_GAP_ANALYSIS.md gap 4, abstractive
    summarization is out of scope until a faithfulness-evaluation
    methodology for short, informal public-comment text is separately
    scoped -- raising here, rather than generating unvalidated text, is
    the correct behavior for this project's current phase."""

    def summarize(self, representative_comment_texts: dict[int, str]) -> SummaryResult:
        from backend.app.ml_interfaces.base import MLComponentNotImplemented

        raise MLComponentNotImplemented(
            "Abstractive summarization is explicitly out of scope for now -- see "
            "research/research_gaps/RESEARCH_GAP_ANALYSIS.md gap 4. Use ExtractiveSummarizer."
        )

"""Policy document retrieval (Phase 3).

A pure-Python Okapi BM25 implementation -- no new dependency installed
(neither `rank_bm25` nor `whoosh` is present in this environment, and
nothing new was added to get this working; BM25 is a well-defined,
simple-enough formula to implement directly over the standard library).

**Kept independent of stance classification by construction**: nothing
in this module imports or references StancePrediction, and retrieval
results never include or depend on any stance label. This is the same
independence principle already established for semantic concern grouping
(docs/architecture/SYSTEM_ARCHITECTURE.md) applied to a different
pipeline.

**No retrieval accuracy is claimed anywhere in this module.** There is no
labeled relevance-evaluation dataset for this corpus (building one would
need its own explicitly-scoped annotation effort, separate from the
stance-annotation one already in progress). Every result carries
provenance (query, method, policy/version scope, timestamp) so a future
evaluation can be run against logged results, but nothing here asserts a
precision/recall number that doesn't exist.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.policy import PolicyDocumentVersion, PolicySection

_TOKEN_RE = re.compile(r"[a-z0-9]+")

BM25_K1 = 1.5
BM25_B = 0.75


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


@dataclass
class RetrievalResult:
    section_id: int
    section_label: str
    score: float
    snippet: str
    policy_document_id: int
    policy_document_version_id: int
    method: str
    query: str
    retrieved_at: datetime


class BM25Index:
    """Built once per retrieval call from a small set of sections (policy
    documents in this project are not large enough to need a persistent
    index -- rebuilding per query is simple, correct, and fast enough at
    this scale; see docs/experiments/HARDWARE_FEASIBILITY_REPORT.md's
    general principle of not over-engineering for a workload that doesn't
    need it)."""

    def __init__(self, documents: list[tuple[int, str]]):
        self.doc_ids = [doc_id for doc_id, _ in documents]
        self.tokenized_docs = [tokenize(text) for _, text in documents]
        self.doc_lengths = [len(toks) for toks in self.tokenized_docs]
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0.0
        self.n_docs = len(documents)

        self.term_doc_freq: dict[str, int] = {}
        for toks in self.tokenized_docs:
            for term in set(toks):
                self.term_doc_freq[term] = self.term_doc_freq.get(term, 0) + 1

    def _idf(self, term: str) -> float:
        df = self.term_doc_freq.get(term, 0)
        # standard BM25 IDF with a +1 floor so a term appearing in every
        # document still gets a small positive weight rather than a
        # negative one.
        return math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1.0)

    def score_all(self, query: str) -> list[tuple[int, float]]:
        query_terms = tokenize(query)
        scores = []
        for i, doc_id in enumerate(self.doc_ids):
            doc_tokens = self.tokenized_docs[i]
            doc_len = self.doc_lengths[i]
            term_counts: dict[str, int] = {}
            for t in doc_tokens:
                term_counts[t] = term_counts.get(t, 0) + 1

            score = 0.0
            for term in query_terms:
                if term not in term_counts:
                    continue
                tf = term_counts[term]
                idf = self._idf(term)
                denom = tf + BM25_K1 * (1 - BM25_B + BM25_B * doc_len / (self.avg_doc_length or 1))
                score += idf * (tf * (BM25_K1 + 1)) / denom
            scores.append((doc_id, score))
        return scores


def _snippet(text: str, query: str, max_len: int = 240) -> str:
    query_terms = set(tokenize(query))
    lower = text.lower()
    best_pos = 0
    for term in query_terms:
        pos = lower.find(term)
        if pos != -1:
            best_pos = max(0, pos - 40)
            break
    snippet = text[best_pos:best_pos + max_len].strip()
    return snippet + ("..." if best_pos + max_len < len(text) else "")


def retrieve_sections(
    db: Session,
    policy_id: int,
    query: str,
    top_k: int = 5,
    policy_document_version_id: Optional[int] = None,
) -> list[RetrievalResult]:
    """BM25 lexical retrieval over a policy's sections. If
    `policy_document_version_id` is omitted, scopes to the latest version
    of the policy document -- metadata/version filtering applied before
    scoring, not after, so results never leak across an unrelated version."""
    if policy_document_version_id is None:
        latest_version_id = db.execute(
            select(PolicyDocumentVersion.id)
            .where(PolicyDocumentVersion.policy_document_id == policy_id)
            .order_by(PolicyDocumentVersion.version_number.desc())
            .limit(1)
        ).scalar_one_or_none()
        policy_document_version_id = latest_version_id

    if policy_document_version_id is None:
        return []  # no ingested document version to retrieve from yet

    sections = db.execute(
        select(PolicySection).where(
            PolicySection.policy_document_id == policy_id,
            PolicySection.policy_document_version_id == policy_document_version_id,
        )
    ).scalars().all()
    if not sections:
        return []

    index = BM25Index([(s.id, s.section_text) for s in sections])
    scores = index.score_all(query)
    scores.sort(key=lambda pair: pair[1], reverse=True)

    sections_by_id = {s.id: s for s in sections}
    retrieved_at = datetime.now(timezone.utc)
    results = []
    for section_id, score in scores[:top_k]:
        if score <= 0:
            continue  # a zero/negative BM25 score means no query term matched at all -- not a result
        section = sections_by_id[section_id]
        results.append(
            RetrievalResult(
                section_id=section.id,
                section_label=section.section_label,
                score=round(score, 4),
                snippet=_snippet(section.section_text, query),
                policy_document_id=policy_id,
                policy_document_version_id=policy_document_version_id,
                method="bm25",
                query=query,
                retrieved_at=retrieved_at,
            )
        )
    return results

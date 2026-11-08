# Experiment Evaluation Framework

**Status:** evaluation methodology for all three principal ML tasks.
No evaluation has been run — **no fabricated evaluation results appear
anywhere in this document.** Every number below is a metric *definition*,
never a reported outcome.

This document formalizes evaluation across stance classification,
semantic grouping, and summarization in one place. Stance classification
and semantic grouping already have task-specific detail in
[`STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md`](STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md)
and [`SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`](SEMANTIC_GROUPING_EXPERIMENT_PLAN.md)
— this document doesn't repeat that detail, it cross-references it and
adds the parts those two plans don't cover (summarization evaluation is
new here; stance and grouping sections below are deliberately short,
pointing back to the fuller plans).

## Stance classification

| Metric | Why it's here |
|---|---|
| **Macro-F1 (primary)** | Per `STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md`'s "Shared setup" — weights all four classes equally regardless of the expected class imbalance (~8–12% Oppose base rate), so poor rare-class performance can't hide behind strong majority-class performance. |
| Per-class precision/recall/F1 | Always reported alongside the macro number, never instead of it — see `RESEARCH_LIMITATIONS.md`'s note that a high macro-F1 doesn't guarantee majority-class strength either. |
| Confusion matrix (4x4) | Qualitative error analysis — specifically checked against which decision rule (D1–D8) an item's `annotation_notes` cites, to see whether errors concentrate on the taxonomy's genuinely hard cases (D2/D3/D4) as hypothesized in `STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md` experiment 3. |
| Balanced accuracy | A secondary summary number, reported alongside macro-F1 for readers more familiar with accuracy-style metrics; never the primary decision criterion, for the same imbalance reason as macro-F1. |
| Baseline comparisons | Every experiment is compared against the TF-IDF baselines (experiments 1–2), never evaluated in isolation — "do not assume the most complex model is the best model" is enforced by *requiring* the comparison, not just allowing it. |

See `STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md` for the full four-experiment
design these metrics apply to.

## Semantic grouping

| Metric | Why it's here |
|---|---|
| Silhouette score | Standard, but a weaker signal for HDBSCAN's variable-density clusters than for K-Means' spherical assumption — reported for both methods with that caveat stated alongside the number, per `SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`. |
| HDBSCAN relative validity index | The more trustworthy metric for the primary (HDBSCAN) run specifically, since it's designed for density-based clustering's own assumptions. |
| **Cluster coverage** (fraction of eligible comments assigned to a non-noise cluster) | Low coverage is a signal worth investigating (embedding/parameter choice, or genuine topic diversity) — reported explicitly, not buried. |
| **Noise ratio** | HDBSCAN's `-1` label, reported as a first-class number, not discarded — see `SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`'s noise-handling section. |
| Cluster coherence | Operationalized as: for a sample of clusters, average pairwise cosine similarity among member embeddings, compared against the same statistic for random same-size samples — a cluster "coheres" if its members are measurably more similar to each other than a random sample would be. |
| Human assessment of cluster quality | A qualitative spot-check (read several member comments per sampled cluster, confirm they plausibly share a concern) — no automatic metric substitutes for this at pilot scale, per `SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`. |
| **Preservation of minority concerns** | Per `RESEARCH_QUESTIONS_AND_HYPOTHESES.md` RQ2/RQ3: does a small cluster (a genuine minority concern) survive as its own group rather than being absorbed into noise or a larger, unrelated cluster? Checked by inspecting the smallest non-noise clusters specifically, not just the largest ones. |

See `SEMANTIC_GROUPING_EXPERIMENT_PLAN.md` for the full pipeline (SBERT →
UMAP where justified → HDBSCAN primary / K-Means comparison) these
metrics apply to, and its explicit note that none of these metrics is a
pass/fail gate — cluster quality is judged by the combination, plus the
human spot-check.

## Summarization

*(New in this document — not covered in depth elsewhere, since
`SYSTEM_ARCHITECTURE.md` component 9 currently scopes summarization to
extractive-only. These metrics are defined now so they're ready the
moment abstractive summarization is explicitly scoped as future work, per
`RESEARCH_GAP_ANALYSIS.md` gap 4 — not because abstractive summarization
is being attempted now.)*

| Metric | Definition | Applies to |
|---|---|---|
| **Evidence coverage** | Fraction of a summary's claims that are directly supported by at least one comment in its `evidence_comment_ids` (per `DATA_MODEL.md`) — for the current extractive-only design, this is trivially 100% by construction (the summary *is* the evidence), which is exactly why extractive is the current default. | Extractive (verified by construction) and abstractive (requires explicit checking) |
| **Factual consistency** | Automatic scoring via a FactCC- or SummaC-style consistency classifier (see `LITERATURE_REVIEW.md` section 9), cross-checked against a human-rated faithfulness sample. **Not evaluated against PolicyLens's own data in this document** — both FactCC and SummaC were validated on news text, not short informal public comments; `RESEARCH_GAP_ANALYSIS.md` gap 4 explicitly flags this domain-transfer question as open. | Abstractive only (future work) |
| **Unsupported-claim rate** | Fraction of summary sentences/clauses that cannot be traced to any evidence comment — the direct, sentence-level counterpart to the hallucination problem described in Ji et al. (2023)'s survey. | Abstractive only (future work) |
| **Redundancy** | Overlap (e.g. ROUGE-L or embedding similarity) between a concern group's summary and its sibling groups' summaries — a high-redundancy pair of "different" concern groups is itself a signal the clustering (not the summarization) may need revisiting. | Both |
| **Human evaluation** | Direct human rating of summary quality/representativeness — see RQ3 in `RESEARCH_QUESTIONS_AND_HYPOTHESES.md` for the specific comparative design (similarity-based selection vs. random baseline). | Both |
| **Traceability** | Every summary's `evidence_comment_ids` resolves to real, existing comments that are genuinely members of the group being summarized — the automated integrity check from RQ4, not a qualitative judgment. | Both, and the only metric in this table that is a hard pass/fail gate rather than a graded score. |

## Cross-cutting evaluation principles

- **No metric here is reported in isolation.** Every table above pairs a
  quantitative score with either a comparison baseline (stance
  classification), a qualitative check (semantic grouping), or an
  explicit scope caveat (summarization) — a lesson taken directly from
  this project's own literature review (e.g. ROUGE alone being
  insufficient to catch unfaithful summaries, per Kryściński et al. 2020).
- **Reproducibility is itself evaluated.** Every experiment records its
  seed, configuration, and input-data hash (the pattern established in
  `ml/stance_classification/dataset_prep.py`'s manifest) — a result that
  can't be reproduced from its own recorded configuration is treated as
  incomplete, not just unlucky.
- **No evaluation result in this project is described as final or
  gold-standard** until the underlying dataset itself clears
  `SINGLE_ANNOTATOR_PROTOCOL.md` section 9's bar — an experiment can
  produce a real, honestly-reported number against a provisional dataset,
  but the dataset's own provisional status is inherited by every
  evaluation run against it, and must be stated alongside the result, not
  left implicit.

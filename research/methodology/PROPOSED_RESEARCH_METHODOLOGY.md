# PolicyLens — Proposed Research Methodology

**Status:** synthesis document. Pulls together dataset provenance,
sampling, annotation, taxonomy, reliability, preprocessing, splitting,
experimentation, evaluation, reproducibility, ethics, and limitations
into one methodology narrative. Each section below states plainly
whether the described work is **completed**, **implemented but not yet
run on real data**, or **planned**.

## 1. Dataset provenance

**Completed.** The canonical corpus
(`data/processed/canonical_corpus/unique_texts.csv`, 10,043 unique
comments) derives from three Government of Canada Open Government
consultation sources (2016–18), documented and hash-verified in
`docs/dataset/MIGRATION_VERIFICATION_REPORT.md`. The corpus is survey/
engagement feedback on Canada's Open Government initiative, not a single
discrete policy document — a fact that shapes every later methodological
choice (see Section 3).

## 2. Sampling

**Completed.** `docs/dataset/SINGLE_ANNOTATOR_PROTOCOL.md` section 4
documents a 250-item, stratified (source_dataset × length-tertile, 9
strata), seeded, reproducible sample from a 7,941-item eligible pool
(English-language, excluding ids already present in three historical
annotation files). A 38-item hidden repeat subset for intra-annotator
reliability is drawn from that sample with a second, independent seed.

## 3. Annotation methodology and taxonomy

**Completed (methodology); in progress (execution).** Four finalized
labels — Support/Oppose/Neutral/Unclear — defined with explicit decision
rules D1–D8 in `docs/dataset/STANCE_LABEL_DEFINITIONS.md`, with a full
workflow, exclusion criteria, and policy-context-adaptation note (since
the corpus has no formal clause-numbered policy document — see
`SINGLE_ANNOTATOR_PROTOCOL.md` section 5) in
`docs/dataset/STANCE_ANNOTATION_GUIDELINES.md`. Execution status: as of
this writing, annotation is actively underway (real progress exists in
`data/annotations/new_experiment/annotation_batch_001.csv`), tracked via
`scripts/annotation/progress.py` / `evaluate.py`.

## 4. Intra-annotator consistency

**Implemented, not yet run.** This project has exactly one human
annotator. Every reliability statistic it can produce is **intra-
annotator (test-retest)**, computed via `scripts/annotation/repeat.py`
once both the full 250-item batch and the 38-item blind, 14-day-gapped
repeat pass are complete — see
`docs/dataset/REPEAT_ANNOTATION_PROCEDURE.md`. **This project explicitly
does not and will not claim inter-annotator agreement** — there is no
second annotator to agree or disagree with. Cohen's kappa is used per the
convention established by Landis &amp; Koch (1977) and surveyed by
Artstein &amp; Poesio (2008), per `research/literature_review/LITERATURE_REVIEW.md`
section 10.

## 5. Data preprocessing

**Implemented.** `ml/stance_classification/dataset_prep.py`'s
`normalize_text()` performs whitespace collapse/trim into a **new**
`normalized_text` field — `comment_text` (the verbatim original) is never
overwritten, enforced structurally by
`scripts/annotation/validate.py`'s immutability check. No other
preprocessing (stemming, stopword removal beyond what a specific
classifier's own vectorizer applies, lowercasing of the source) is
applied to the stored data — any such transform is scoped to a
classifier's own feature-extraction step (e.g. `TfidfVectorizer`'s
internal tokenization), never to the shared, persisted comment record.

## 6. Train/validation/test separation

**Implemented, not yet run on real data.**
`ml/stance_classification/dataset_prep.py`'s `make_splits()` performs a
**group-aware** (duplicate-text-safe), **stratified** (by stance label),
**seeded** 70/15/15 split, with an independent `validate_splits.py`
auditor re-checking the result from scratch — never trusting its own
manifest's self-report. Refuses to run until a genuine finalized
annotation export exists (`scripts/annotation/finalize.py`'s output);
there is currently nothing to split, by design.

## 7. Experimental comparisons

**Planned, not run.** Four stance-classification experiments (TF-IDF +
LogReg, TF-IDF + LinearSVC, SBERT + classifier, conditional transformer
fine-tuning) and a semantic-grouping pipeline (SBERT → UMAP where
justified → HDBSCAN primary / K-Means comparison), detailed in
`docs/experiments/STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md` and
`docs/experiments/SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`, with an explicit
instruction against assuming the most complex model wins by default.

## 8. Evaluation

**Framework defined, no results exist.**
`docs/experiments/EXPERIMENT_EVALUATION_FRAMEWORK.md` specifies macro-F1/
per-class metrics/confusion matrix/balanced accuracy for classification;
silhouette/validity-index/coverage/noise-ratio/coherence/human-assessment/
minority-preservation for grouping; evidence-coverage/factual-consistency/
unsupported-claim-rate/redundancy/human-evaluation/traceability for any
future summarization work.

## 9. Reproducibility

**Implemented.** Every seeded operation in this project (the 250-item
stratified sample, the 38-item repeat-subset draw, the repeat-pass
reshuffle, the train/val/test split) records its exact seed and
configuration. File hashes are recorded at every handoff point
(`protected_baseline.json` for historical/corpus files,
`finalize.py`'s reproducibility report, `dataset_prep.py`'s
`split_manifest.json`) so any later step can verify it's building on
exactly the data it thinks it is, not a silently-changed version.

## 10. Ethical considerations

**New in this document.** Several considerations follow directly from
this project's own design choices and from what the literature review
surfaced:

- **Public record vs. re-identification risk.** The source comments are
  already-published government consultation responses, not newly
  collected private data — but `SYSTEM_ARCHITECTURE.md` component 3
  (data validation and privacy filtering) still treats PII detection as
  a required flag-for-review step, not an assumption that "already
  public" means "safe to process and redisplay without any check."
  `RESEARCH_GAP_ANALYSIS.md` gap 6 honestly notes this project has not
  yet conducted a dedicated literature search on privacy-preserving
  public-feedback datasets specifically — that search should precede any
  live deployment handling real submitter-identifiable data.
- **Not uniformly beneficial.** The literature review surfaced a
  documented counter-example (a Sunlight Foundation observation that NLP
  added little value for one FCC consultation whose comment interface was
  already highly structured) — this project should not assume its
  tooling is valuable for every consultation design, and should say so
  rather than oversell general applicability.
- **Single-annotator subjectivity is disclosed, not hidden.** Every
  artifact this project produces from the current annotation batch
  carries an explicit "intra-annotator only, not inter-annotator, not
  gold-standard" statement (see `finalize.py`'s and `dataset_prep.py`'s
  own output). A stance label reflects one person's judgment under a
  documented taxonomy — this is disclosed at every handoff point, not
  asserted as objective ground truth.
- **Minority and dissenting views must not be algorithmically erased.**
  `RESEARCH_GAP_ANALYSIS.md` gap 3 and `RESEARCH_QUESTIONS_AND_HYPOTHESES.md`
  RQ2/RQ3 exist specifically because a policy-analytics tool that
  aggregates public comment risks making a minority viewpoint
  statistically invisible — HDBSCAN's noise category (reported, not
  hidden) and the explicit stance-mixture check within concern clusters
  are direct, designed countermeasures to that risk, not afterthoughts.
- **No automated system's output replaces human judgment of a policy's
  merits.** `PolicyReport` (per `DATA_MODEL.md`) is designed to inform
  human policymakers, not to issue an automated verdict on a policy — no
  component in `SYSTEM_ARCHITECTURE.md` is scoped as a decision-maker.

## 11. Limitations

Consolidated separately, in full, at
[`../../docs/experiments/RESEARCH_LIMITATIONS.md`](../../docs/experiments/RESEARCH_LIMITATIONS.md) —
not duplicated here to avoid the two documents drifting out of sync.

## What is completed vs. planned, at a glance

| Section | Status |
|---|---|
| 1. Dataset provenance | Completed |
| 2. Sampling | Completed |
| 3. Annotation methodology | Completed (methodology); annotation itself in progress |
| 4. Intra-annotator consistency | Implemented, awaiting real second pass |
| 5. Preprocessing | Implemented |
| 6. Train/val/test separation | Implemented, awaiting real finalized data |
| 7. Experimental comparisons | Planned only |
| 8. Evaluation framework | Defined, no results |
| 9. Reproducibility | Implemented |
| 10. Ethical considerations | Documented here for the first time |
| 11. Limitations | See `RESEARCH_LIMITATIONS.md` |

# Research Limitations

A consolidated, honest list of this project's current limitations, pulled
together from the annotation methodology, the ML dataset architecture,
and the two experiment plans, so they live in one place rather than being
scattered (or quietly omitted) across documents.

## Annotation methodology

- **Single annotator.** Every reliability figure this project can ever
  produce is intra-annotator (test-retest), never inter-annotator
  agreement. There is no second human perspective anywhere in this
  dataset's construction. See `SINGLE_ANNOTATOR_PROTOCOL.md` section 7.
- **Pilot-scale sample size.** 250 items, stratified but not huge — rare
  classes (an estimated 8–12% Oppose base rate) will have thin counts
  (roughly 20–30 examples), enough to pilot the guidelines against, not
  enough for confident prevalence estimates. See
  `SINGLE_ANNOTATOR_PROTOCOL.md` section 4.2 and section 10.
- **Historical "reference" files are of unverified provenance.** The
  pre-existing 600-row and 400-row datasets show literally zero annotator
  disagreement across hundreds of rows each — a pattern inconsistent with
  genuine independent double-annotation on a nuanced 4-class task. They
  are treated as calibration material, not validated ground truth. See
  `SINGLE_ANNOTATOR_PROTOCOL.md` section 2.
- **No formal policy document exists for this corpus.** The corpus is
  Government of Canada Open Government consultation/survey feedback, not
  a single policy with numbered clauses. Rule D6 ("consult the policy
  document") is satisfied by the richest available metadata
  (`policy_context`/`policy_section`), not a literal clause-numbered
  document. See `SINGLE_ANNOTATOR_PROTOCOL.md` section 5 and section 10.
- **Non-English comments are out of scope for the current batch**
  (~10.9% of the otherwise-eligible pool), pending confirmation of the
  annotator's working-language proficiency. See
  `SINGLE_ANNOTATOR_PROTOCOL.md` section 10.
- **Annotation-time estimates are a rough proxy, not a measurement** — see
  `scripts/annotation/timing.py`'s own documented limitations (gaps
  between saves conflate "thinking time" with "time away from the
  keyboard"; reordered work breaks the simple interpretation; a fixed
  break-length heuristic is a heuristic, not a certainty).

## ML dataset preparation

- **Nothing to prepare yet.** `ml/stance_classification/dataset_prep.py`
  refuses to run until a finalized annotation export exists — this is by
  design, not an oversight, but it does mean every claim in the two
  experiment plans is currently hypothetical, pending real data.
- **Group-level (duplicate-text) splitting trades off a small amount of
  exact stratification precision for leakage safety** — a stance label
  distribution that's skewed by one very common duplicated phrase could
  pull an entire text-group, and its label, into one split rather than
  spreading proportionally. This is the right trade given the alternative
  (leakage) is worse, but it means split-level label proportions are
  "close to" the overall distribution, not guaranteed exact.
- **Only one dedup signal (exact normalized-text match) is used.** Near-
  duplicates that differ by more than whitespace/case (e.g. paraphrases)
  are not detected by `dataset_prep.py`'s current leakage check — this is
  a narrower leakage guard than a semantic-similarity-based one would be,
  deliberately kept simple and auditable rather than probabilistic.

## Stance classification plan

- **No experiment has run.** Every expected-outcome statement in
  `STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md` is a hypothesis, not a
  result.
- **Transformer fine-tuning (experiment 4) is likely not justified at the
  current dataset scale or on this hardware** — see
  `HARDWARE_FEASIBILITY_REPORT.md`. This is stated as the plan's own
  expectation, not a finding.
- **Macro-F1 as the primary metric is itself a choice with a trade-off:**
  it weights a class with 20 examples equally with a class with 100,
  which is the right call for catching poor rare-class performance, but
  means a high macro-F1 doesn't guarantee strong performance on the
  majority class either — both the macro number and the per-class
  breakdown should always be read together, never the macro number alone.

## Semantic grouping plan

- **No clustering has run.** Same caveat as above — hypotheses, not
  results.
- **Cluster counts/shapes are expected to be unstable at pilot scale** —
  the plan itself recommends multi-seed re-runs rather than trusting one
  run's output, precisely because instability at this data scale is
  expected, not a sign of a broken method.
- **Clustering quality metrics (silhouette, HDBSCAN validity index) are
  diagnostic aids, not pass/fail thresholds** — there is no number in
  this project's plans that, crossed, certifies a clustering run as
  "correct." Qualitative review of representative comments remains
  necessary.

## Cross-cutting

- **No gold-standard claim exists anywhere in this project for the new
  single-annotator dataset**, and none should be made until
  `SINGLE_ANNOTATOR_PROTOCOL.md` section 9's conditions are met (kappa
  computed and acceptable, systematic disagreements reviewed). Every
  tool that touches this dataset (`finalize.py`, `dataset_prep.py`,
  `validate_splits.py`) carries this statement explicitly in its output
  rather than leaving it to be assumed.
- **Nothing in this project has been trained, fine-tuned, or evaluated as
  a model** as of this writing. Every "expected" or "hypothesized"
  outcome in the two experiment plans is exactly that — a stated
  expectation to be tested, not a result being reported.

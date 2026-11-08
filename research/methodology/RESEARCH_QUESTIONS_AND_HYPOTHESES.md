# PolicyLens — Research Questions and Hypotheses

**Status:** research design document. Builds directly on
[`../research_gaps/RESEARCH_GAP_ANALYSIS.md`](../research_gaps/RESEARCH_GAP_ANALYSIS.md).
Each question below is phrased as something this project can actually
test with data it can realistically obtain — not an open-ended aspiration.

---

## RQ1 — Does policy context improve stance classification compared with text-only classification?

- **Hypothesis:** including `policy_context`/`policy_section` text as part
  of a classifier's input yields higher macro-F1 than comment text alone,
  because rule D6 (`STANCE_LABEL_DEFINITIONS.md`) establishes that some
  comments are only correctly interpretable with policy context (e.g.
  comments referencing a specific provision, clause, or threshold).
- **Independent variable:** input representation — (a) `normalized_text`
  only, vs. (b) `normalized_text` concatenated with (or jointly encoded
  alongside) `policy_context` + `policy_section`.
- **Dependent variable:** macro-F1 on a held-out validation/test split
  (same split, same seed, varying only the input representation).
- **Experimental design:** an ablation, not a new architecture — run
  `STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md` experiment 3 (SBERT +
  classifier) twice, once per input representation, holding the
  classifier, seed, and split fixed.
- **Evaluation metrics:** macro-F1 (primary), per-class F1, with specific
  attention to whether the gap (if any) concentrates on comments whose
  `annotation_notes` cite rule D6 — a direct, traceable test of the
  hypothesis's actual mechanism, not just an aggregate number.
- **Required data:** a finalized, labeled dataset (does not exist yet).
- **Limitations:** at pilot scale (~250 items), statistical power to
  detect a modest effect is low; a null result at this scale doesn't rule
  out a real effect at larger scale. **Cannot begin until human
  annotation (data/annotations/new_experiment/) is complete and
  finalized.**

---

## RQ2 — Can concern grouping preserve comments expressing different stances?

- **Hypothesis:** clustering comments by semantic concern (independent of
  stance, per `SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`'s design) produces
  concern groups that are **not** stance-homogeneous — i.e., real concern
  groups contain a genuine mix of Support/Oppose/Neutral/Unclear comments,
  confirming the grouping captures topic rather than accidentally
  re-deriving sentiment/stance as a side effect.
- **Independent variable:** none manipulated — this is an observational
  question about the clustering's actual output, not a comparison between
  conditions.
- **Dependent variable:** the stance-label distribution (entropy or
  simple proportion spread) within each non-noise concern group.
- **Experimental design:** run HDBSCAN clustering (`SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`)
  on the eligible comment pool, independently run stance classification
  (human-labeled, or model-predicted once available) on the same pool,
  then cross-tabulate group membership against stance label — a join
  performed strictly after both pipelines have run independently, per the
  architecture's non-negotiable separation.
- **Evaluation metrics:** per-group stance entropy; fraction of non-noise
  groups that are stance-homogeneous (a high fraction would be a warning
  sign, not a success).
- **Required data:** both a labeled stance dataset AND clustering output
  over the same comments — needs human annotation to finish first, but
  the clustering half can, in principle, run on **unlabeled** comments
  today (clustering requires no stance labels as input at all) — so the
  clustering side of this question is **not** blocked on annotation
  completion, only the cross-tabulation step is.
- **Limitations:** at 250 items, cluster sizes will likely be small
  enough that entropy estimates are noisy; this question is better
  answered at the fuller 7,941-item eligible-pool scale once more
  annotation exists.

---

## RQ3 — Can representative/extractive summaries retain the important evidence and viewpoints of original comments?

- **Hypothesis:** a small set (3–5) of embedding-similarity-selected
  representative comments per concern group captures the group's stance
  diversity and substantive content at least as well as a larger random
  sample of the same size would — i.e., similarity-based selection is not
  worse than chance at representativeness, and ideally better.
- **Independent variable:** selection method — (a) similarity-to-
  centroid/medoid (the plan's default), vs. (b) random sampling within
  the group, as a baseline comparison.
- **Dependent variable:** human-rated representativeness (does this
  sample reflect what the full group is actually saying?) and coverage
  of the group's stance distribution (does the sample include examples of
  each stance present in the full group, not just the majority one?).
- **Experimental design:** for a sample of concern groups, generate both
  selections, present both (blinded, order-randomized) to a human
  reviewer alongside the full group, and record which is rated more
  representative — a small human evaluation study, not an automatic
  metric alone.
- **Evaluation metrics:** human preference rate; stance-coverage rate
  (fraction of groups where the representative sample includes every
  stance label present in the full group, for groups small enough that
  this is achievable at sample size 3–5).
- **Required data:** finished clustering output over a labeled dataset —
  blocked on both annotation completion and clustering having run.
- **Limitations:** human evaluation at any meaningful scale requires
  annotator time this project has already identified as scarce (one
  annotator); this question may need to wait until annotation capacity
  frees up after the primary stance-labeling task.

---

## RQ4 — How can individual comments be traced back from aggregate analytical outputs?

- **Hypothesis:** a schema-level traceability guarantee (every
  `Summary`/`PolicyReport`/`ConcernGroup` reference resolvable to real
  comment records, per `DATA_MODEL.md`) can be verified by an automated,
  independent integrity check — modeled directly on
  `ml/stance_classification/validate_splits.py`'s existing pattern of
  re-validating a pipeline's output from scratch rather than trusting its
  own self-report.
- **Independent variable:** none — this is a structural verification
  question, not a comparative experiment.
- **Dependent variable:** whether the integrity check passes (binary,
  per-reference) across every `Summary`/`PolicyReport`/`ConcernGroup` in
  a given run's output.
- **Experimental design:** build the integrity checker described in
  `SYSTEM_ARCHITECTURE.md` component 11 and run it against any pipeline
  output that exists at the time — this one is **not** blocked on
  annotation completion in the same way as RQ1–3: the checker itself can
  be built and unit-tested today against synthetic fixture data (the same
  approach already used throughout `tests/unit/` and `tests/integration/`
  for the annotation and dataset-prep subsystems), and only needs real
  pipeline output to run against real data once downstream components
  (clustering, summarization) are actually implemented.
- **Evaluation metrics:** pass/fail count of broken references; this is a
  correctness check, not a metric with a "good enough" threshold — any
  broken reference is a bug, full stop.
- **Required data:** none required to build and test the checker itself;
  real pipeline output required only to run it against real data.
- **Limitations:** this question only verifies that traceability *links*
  resolve — it does not verify that a summary's *content* is faithful to
  its evidence (that's RQ3's territory, and the evidence-grounded-
  summarization gap from the gap analysis).

---

## Which experiments can begin today vs. which are blocked

| Question | Blocked on human annotation completion? |
|---|---|
| RQ1 (policy-context ablation) | **Yes** — needs a finalized labeled dataset. |
| RQ2 (stance-mixture within clusters) | Clustering half: **no** (needs only embeddings, not labels). Cross-tabulation half: **yes**. |
| RQ3 (representative-comment quality) | **Yes** — needs labeled data and completed clustering. |
| RQ4 (traceability integrity checker) | **No** — the checker itself can be built and tested against synthetic fixtures now; only running it against real pipeline output requires real data and an implemented pipeline. |

This table is the concrete answer to "clearly identify which experiments
cannot begin until the human annotations are complete" — three of four
research questions are genuinely gated on annotation; one (building and
unit-testing the traceability checker) is not, and is a reasonable next
engineering task independent of annotation progress.

# ML Experiment Roadmap

**Status:** planning document. Ties together the annotation workflow, the
ML dataset preparation architecture, and the two experiment plans into one
ordered sequence with explicit go/no-go gates. **No model has been
trained anywhere in this project.**

## The sequence, and why each gate exists

```
[1] Single-annotator annotation (data/annotations/new_experiment/)
      |  GATE: all 250 items labeled or excluded
      v
[2] 14-day wait + hidden repeat pass (intra-annotator reliability)
      |  GATE: repeat.py kappa succeeds (both passes complete)
      v
[3] Review kappa against SINGLE_ANNOTATOR_PROTOCOL.md section 9's bar
      |  GATE: human review -- accept, or revise guidelines and re-annotate
      |        the disagreeing items (not a silent pass-through)
      v
[4] finalize.py -- validated, hash-recorded export
      |  GATE: finalize.py's own completeness + immutability checks
      v
[5] ml/stance_classification/dataset_prep.py -- leakage-checked splits
      |  GATE: validate_splits.py reports zero problems
      v
[6] Stance classification experiments 1-3 (TF-IDF x2, SBERT+classifier)
      |  GATE: compare macro-F1; only proceed to [7] if a meaningful,
      |        reproducible gap favors going further
      v
[7] (conditional) Transformer fine-tuning experiment 4
      |        -- only with more data and/or GPU hardware, per
      |        HARDWARE_FEASIBILITY_REPORT.md

[A] Semantic grouping (independent branch -- does not wait on [6]/[7])
      runs off the same eligible-comment pool and embedding cache as [6],
      but produces concern clusters, never stance labels.
```

**Why gates, not a straight pipeline:** every gate above corresponds to a
restriction this project has been explicit about from the start (don't
call anything gold-standard before validation; don't train on an
incomplete or leaking dataset; don't assume the most complex model wins).
Encoding them as explicit stop points, rather than trusting later steps to
"just work," is the point of writing this roadmap down instead of only
writing the code.

## Current position on the roadmap

As of this writing: **step [1], not yet complete** (0/250 items
annotated — see
[`EXPERIMENT_STATUS_REPORT.md`](../dataset/EXPERIMENT_STATUS_REPORT.md)).
Everything from step [1] onward is implemented and tested in advance
(`scripts/annotation/`, `ml/stance_classification/dataset_prep.py` +
`validate_splits.py`, 120 passing automated tests) so that once real
annotations exist, the remaining steps are a matter of running already-
built, already-validated tooling — not building it under time pressure
with genuine data on the line.

## Decision criteria for "is this experiment worth running"

Before spending CPU time (or, for experiment 4, a meaningful chunk of an
8 GB machine's headroom) on any classification experiment:

1. Does the finalized dataset actually have enough examples of each class
   to make the comparison meaningful? (`evaluate.py`'s stance distribution
   output answers this directly once annotations exist.)
2. Did the repeat-annotation kappa (step [2]/[3]) come back acceptable? A
   classifier trained against a self-inconsistent single annotator inherits
   that inconsistency as noise — worth running at any kappa level for
   signal, but worth *interpreting cautiously* if kappa is low, not worth
   pretending is "clean ground truth" regardless of the number.
3. Does `validate_splits.py` report zero leakage problems? This is a hard
   gate, not a soft check — a leaking split invalidates any metric computed
   from it.

## What this roadmap deliberately does not promise

- **No timeline.** Step [1] depends entirely on the project owner's actual
  annotation pace, which this document has no way to estimate reliably
  (see `EXPERIMENT_STATUS_REPORT.md`'s timing-tracking caveats).
  Step [2] has a hard minimum of 14 days by design, not a maximum.
- **No promised accuracy/F1 target.** Per `STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md`,
  this is a genuine comparison, not a plan to hit a pre-chosen number.
- **No commitment to transformer fine-tuning.** Step [7] is explicitly
  conditional and may reasonably never happen on this hardware.

## Related documents

- [`STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md`](STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md)
- [`SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`](SEMANTIC_GROUPING_EXPERIMENT_PLAN.md)
- [`HARDWARE_FEASIBILITY_REPORT.md`](HARDWARE_FEASIBILITY_REPORT.md)
- [`RESEARCH_LIMITATIONS.md`](RESEARCH_LIMITATIONS.md)
- [`../dataset/SINGLE_ANNOTATOR_PROTOCOL.md`](../dataset/SINGLE_ANNOTATOR_PROTOCOL.md)
- [`../dataset/ANNOTATION_WORKFLOW.md`](../dataset/ANNOTATION_WORKFLOW.md)

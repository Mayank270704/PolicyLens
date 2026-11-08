# Single-Annotator Experiment — Status Report

**Last updated:** 2026-11-08 (tooling implementation date; update this line
whenever status materially changes).

## Current status: tooling complete, annotation not started

| Stage | Status |
|---|---|
| Sampling design & protocol | Done — `SINGLE_ANNOTATOR_PROTOCOL.md` |
| `annotation_batch_001.csv` (250 rows) generated | Done, all 250 rows blank |
| `repeat_annotation_plan.json` (38-item hidden subset) generated | Done |
| Original blank-batch backup | Done — `annotation_batch_001.original_backup.csv` |
| Protected file-hash baseline | Done — `protected_baseline.json` (5 files tracked) |
| Validation tooling (Task 1) | Implemented, tested |
| Progress tooling (Task 2) | Implemented, tested |
| Annotation interface (Task 3) | Implemented, smoke-tested |
| Repeat-annotation tooling (Task 4) | Implemented, tested (gate + kappa logic; no real second pass exists yet) |
| Finalization/export tooling (Task 5) | Implemented, tested |
| Test suite (Task 6) | 72/72 passing |
| Documentation (Task 7) | This file + 4 companion docs |
| **First-pass human annotation (250 items)** | **Not started — 0/250 labeled or excluded** |
| 14-day repeat gate | Not open (first pass not complete) |
| Intra-annotator kappa | Not computed — no second pass exists |
| Finalized export | Not produced — `finalize.py` correctly refuses while the batch is incomplete |

## Snapshot (reproducible via `python scripts/annotation/progress.py`)

```
Total comments:      250
Annotated (stance):  0
Excluded:            0
Pending:             250
Completion:          0.0%
```

## What is and isn't claimed right now

- **No stance label exists yet.** Nothing in this repository should be read
  as a stance prediction or ground truth for any of the 250 sampled
  comments.
- **No gold-standard claim is made or implied anywhere in this tooling.**
  `finalize.py`'s reproducibility report explicitly states
  `"gold_standard_claim": "NOT MADE"` and will continue to say so until the
  conditions in `SINGLE_ANNOTATOR_PROTOCOL.md` section 9 are met.
- **No inter-annotator agreement is claimed or computable.** This is a
  single-annotator experiment; the only agreement statistic this tooling
  can ever produce is intra-annotator (test-retest) kappa, and only once a
  genuine, time-gapped second pass exists.
- **The three pre-existing historical files remain unmodified**, verified
  by SHA-256 against `protected_baseline.json`:
  `consolidated_stance_dataset_corrected.csv`,
  `stance_human_gold_400_provisional.csv`,
  `stance_targeted_master.csv` (+ its byte-identical blind copy), plus the
  canonical corpus `unique_texts.csv` itself.

## Next actions

1. Run `python scripts/annotation/setup.py` once (idempotent; already run —
   re-running is harmless and just re-confirms the baseline).
2. Begin first-pass annotation: `python scripts/annotation/gui.py`.
3. Check progress periodically: `python scripts/annotation/progress.py`.
4. After 250/250 and a 14-day wait, follow
   `REPEAT_ANNOTATION_PROCEDURE.md` for the hidden repeat pass.
5. Run `python scripts/annotation/finalize.py` only once both the main
   batch and (if desired before finalizing) the repeat pass are complete.

See `ANNOTATION_WORKFLOW.md` for the full command sequence and design
rationale.

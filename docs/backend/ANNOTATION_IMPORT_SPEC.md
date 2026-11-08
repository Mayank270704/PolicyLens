# Annotation Import Specification

`backend/app/services/annotation_import.py` consumes a CSV in **exactly**
the schema `scripts/annotation/finalize.py` produces
(`data/annotations/new_experiment/finalized/stance_annotations_final.csv`)
and maps each row into this backend's `Comment` + `StancePrediction`
tables.

**No finalized export exists yet** — annotation is still in progress
(56/250 as of this writing; see
`docs/dataset/EXPERIMENT_STATUS_REPORT.md`). This adapter has been built
and fully tested against **synthetic fixture rows only**
(`tests/unit/test_annotation_import.py`,
`tests/integration/test_full_workflow.py`), shaped identically to the
real schema but containing fabricated text and labels, clearly not real
annotations. It will work unchanged once a genuine finalized export
exists — no adapter code changes are anticipated at that point.

## Expected input schema (exact match to `finalize.py`'s output)

| Column | Maps to |
|---|---|
| `comment_id` | Not stored directly (the backend assigns its own `Comment.id`); used only in error messages for traceability back to the source file. |
| `comment_text` | `Comment.original_text` (verbatim). |
| `policy_context`, `policy_section` | Not currently stored (this backend's `PolicySection` model expects to be tied to an ingested `PolicyDocument`; a future enhancement could attempt to match these free-text fields to an ingested section, but that matching is not implemented — out of scope for this import adapter). |
| `annotator_label` | `StancePrediction.label`. |
| `exclusion_code` | `StancePrediction.exclusion_code`. |
| `annotation_confidence` | `StancePrediction.confidence` (cast to int). |
| `annotation_notes` | `StancePrediction.notes`. |
| `source_unique_id` + `source_dataset` | Together form the idempotency/dedup key via `CommentSourceMetadata` — matches the canonical corpus's own `unique_id` concept. |
| `language` | `Comment.language`. |
| `word_count` | Not stored (derivable from `original_text` if ever needed; storing it separately would risk drifting out of sync with the text). |

Every `StancePrediction` created this way has `source="human"` and
`pass_number=1` — this adapter does not attempt to distinguish a first
pass from the hidden repeat-subset's second pass (see
`docs/dataset/REPEAT_ANNOTATION_PROCEDURE.md`); importing a genuine
second-pass file would need a second, explicit import call with
`pass_number=2`, which is not yet built (no second pass exists yet
either, so this hasn't been needed).

## Independent re-validation — never trust "finalized" at face value

Before mapping any row, this adapter re-checks, from scratch, exactly the
structural rules `scripts/annotation/validate.py` already enforces on the
CSV side:

- `annotator_label` and `exclusion_code` are mutually exclusive (rule D8).
- Exactly one of them must be set — a row with **neither** is rejected as
  "not actually finalized," even though it arrived in a file called
  "finalized."
- `annotator_label` must be one of the four taxonomy values; `exclusion_code`
  must be one of the four defined codes; `annotation_confidence` (if
  present) must be `1`/`2`/`3`.

This mirrors `ml/stance_classification/validate_splits.py`'s
already-established pattern: a downstream consumer of a pipeline's output
re-audits that output independently rather than assuming it's correct
because of where it came from.

## Idempotency

Re-importing the identical file is safe: both the `Comment` (keyed on
`source_dataset` + `source_unique_id`) and the `StancePrediction` (keyed
on `comment_id` + `annotator_or_model_ref` + `pass_number`) are checked
for existence before creating a new row — a second import of the same
file produces zero new rows, reported explicitly as
`comments_reused`/`skipped_already_imported_count` rather than silently
duplicating data.

## What this adapter will never do

- Generate, infer, or guess a label for a row that doesn't have one.
- Treat a pseudo-labeled or AI-predicted file as if it were human
  annotation — the only `source` value this adapter ever writes is
  `"human"`.
- Modify `scripts/annotation/finalize.py`'s output file itself (read-only
  consumption).

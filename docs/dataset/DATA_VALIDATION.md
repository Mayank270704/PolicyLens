# Annotation Data Validation

`scripts/annotation/validate.py` implements Task 1 of the annotation
workflow: structural and consistency checks over a batch CSV. It never
assigns a label — it only reports problems, each as either an `ERROR`
(blocking) or a `WARNING` (worth a look, non-blocking).

## Running it

```
python scripts/annotation/validate.py
python scripts/annotation/validate.py --batch <path> --backup <path>
python scripts/annotation/validate.py --require-complete   # as used before finalization
```

Exit code is `0` if there are zero errors, `1` otherwise (warnings never
affect the exit code).

## Checks performed

| Check | Severity | Trigger |
|---|---|---|
| `MISSING_COLUMNS` | ERROR | Any of the 12 required columns (`comment_id`, `comment_text`, `policy_context`, `policy_section`, `annotator_label`, `exclusion_code`, `annotation_confidence`, `annotation_notes`, `source_unique_id`, `source_dataset`, `language`, `word_count`) is absent from the header. |
| `MISSING_ID` | ERROR | `comment_id` is blank. |
| `ID_FORMAT` | WARNING | `comment_id` doesn't start with the `PL-` stable-ID prefix. |
| `DUPLICATE_ID` | ERROR | The same `comment_id` appears on more than one row. |
| `INVALID_WORD_COUNT` | ERROR | `word_count` isn't parseable as an integer. |
| `INVALID_LABEL` | ERROR | `annotator_label` is set to something other than one of the four finalized labels (`Support`/`Oppose`/`Neutral`/`Unclear`) or blank. |
| `INVALID_EXCLUSION_CODE` | ERROR | `exclusion_code` is set to something other than one of the four codes (`SPAM`/`OFF_TOPIC`/`TOO_SHORT_NONSUBSTANTIVE`/`UNINTELLIGIBLE`) or blank. |
| `LABEL_AND_EXCLUSION_SET` | ERROR | Both `annotator_label` and `exclusion_code` are non-blank on the same row — these two fields are mutually exclusive (rule D8: a comment is either excluded, or labeled, never both). |
| `INVALID_CONFIDENCE` | ERROR | `annotation_confidence` is set to something other than `1`/`2`/`3` or blank. |
| `MISSING_CONFIDENCE` | WARNING | A stance label is set but confidence is blank. |
| `MISSING_REQUIRED_NOTES` | ERROR | `annotator_label` is `Unclear` and `annotation_notes` is blank (required per `STANCE_ANNOTATION_GUIDELINES.md` section 3, step 9). |
| `NOTES_RECOMMENDED` | WARNING | `annotator_label` is `Oppose` and notes are blank — required *if* the label was reached via rule D4, which this tool has no way to detect automatically, so it's a warning, not an error. |
| `INCOMPLETE` | ERROR, only with `--require-complete` | A row has neither a stance label nor an exclusion code. Not an error during normal annotation (rows are legitimately pending); becomes an error for the pre-finalization check. |
| `IMMUTABLE_FIELD_CHANGED` | ERROR, only when a backup is supplied | Any of `comment_id`/`comment_text`/`policy_context`/`policy_section`/`source_unique_id`/`source_dataset`/`language`/`word_count` differs from the value recorded in the original blank-batch backup. |
| `ID_NOT_IN_BACKUP` | ERROR, only with a backup | A `comment_id` exists in the working file that wasn't in the original backup (an unauthorized insertion). |
| `ID_MISSING_FROM_BATCH` | ERROR, only with a backup | A `comment_id` from the original backup is missing from the working file (an unauthorized deletion). |

## Why exclusion codes and stance labels are two columns, not one

Per `STANCE_LABEL_DEFINITIONS.md` rule D8 and
`STANCE_ANNOTATION_GUIDELINES.md` section 5, exclusion is decided **before**
any stance reasoning, and an excluded comment never receives a stance label
— not even `Neutral`. Modeling this as two separate, mutually-exclusive
columns (rather than, say, adding `EXCLUDED` as a fifth value of one
`label` column) makes "accidentally labeling something that should have
been excluded" a structurally-checkable condition
(`LABEL_AND_EXCLUSION_SET`) rather than a judgment call about whether a
value belongs to one taxonomy or another.

## Why immutability is checked against a backup, not inferred

There's no way to tell, from a single CSV snapshot alone, whether
`comment_text` was edited after generation — it could be the original text
or a later "correction." The original, all-blank batch is backed up once
(see `ANNOTATION_INTERFACE_GUIDE.md`) specifically so every later state can
be diffed against a known-good baseline. `finalize.py` calls this check
with `require_complete=True` and refuses to export if it finds any
discrepancy.

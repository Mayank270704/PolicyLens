# Migration Verification Report

**Scope:** Read-only audit comparing files migrated from the previous
PolicyLens project (`C:\Users\MAYANK SWAROOP\OneDrive\Desktop\dataset`) into
the current project (`C:\Users\MAYANK SWAROOP\OneDrive\Desktop\PolicyLens`).

**Method:** For every expected file, both the source and destination copies
were located, their file sizes compared, and SHA-256 hashes computed and
compared byte-for-byte. CSV files were additionally parsed (Python's
built-in `csv` module) to confirm readability and report row/column counts.
No source or destination file content was modified. No files were moved,
renamed, or overwritten. No dependencies were installed (verification used
Python's standard library only, run with `-I` isolated mode).

## Summary

| Metric | Value |
|---|---|
| Total expected files | 18 |
| Successfully verified (hash match) | 18 |
| Missing files (not found at source or destination) | 0 |
| Hash mismatches | 0 |
| Source files unavailable | 0 |
| Destination path discrepancies (file present, wrong folder) | 4 (Group E) |
| CSV files unreadable | 0 |
| **Overall migration status** | **PASS, with one non-blocking path discrepancy (Group E)** |

All 18 expected files exist at the source, exist somewhere at the
destination, and are byte-identical to their source copies (matching size
and SHA-256). The only issue found is structural, not a data-integrity
issue: the four Group E files were written one directory level higher than
the path specified in the migration plan.

## A. Original raw datasets — `data/raw/original_sources/`

| File | Source | Dest | Size match | SHA-256 match |
|---|---|---|---|---|
| Open Government Consultation Data 2017-18 Get Involved Questionnaire.csv | ✅ | ✅ | ✅ | ✅ |
| ap2016-18_individual_comments.csv | ✅ | ✅ | ✅ | ✅ |
| ConsultationData2017Engagement_Donnéesdesconsultations2017engagements.csv | ✅ | ✅ | ✅ | ✅ |

All three files verified at the expected destination path. No discrepancies.

## B. Canonical corpus — `data/processed/canonical_corpus/`

| File | Source | Dest | Size match | SHA-256 match |
|---|---|---|---|---|
| unique_texts.csv | ✅ | ✅ | ✅ | ✅ |
| corpus_entries.csv | ✅ | ✅ | ✅ | ✅ |
| unique_texts_labeled.csv | ✅ | ✅ | ✅ | ✅ |
| reconciliation.csv | ✅ | ✅ | ✅ | ✅ |
| corpus_manifest.json | ✅ | ✅ | ✅ | ✅ |

All five files (all were available in source) verified at the expected
destination path. No discrepancies.

## C. Previous stance annotations — `data/annotations/previous_research/`

| File | Source | Dest | Size match | SHA-256 match |
|---|---|---|---|---|
| consolidated_stance_dataset.csv | ✅ | ✅ | ✅ | ✅ |
| consolidated_stance_dataset_corrected.csv | ✅ | ✅ | ✅ | ✅ |
| stance_human_gold_400_provisional.csv | ✅ | ✅ | ✅ | ✅ |

All three files (all were available in source) verified at the expected
destination path. No discrepancies.

## D. Targeted annotation files — `data/annotations/previous_research/targeted_annotation_200/`

| File | Source | Dest | Size match | SHA-256 match |
|---|---|---|---|---|
| sampling_manifest.json | ✅ | ✅ | ✅ | ✅ |
| stance_targeted_master.csv | ✅ | ✅ | ✅ | ✅ |
| stance_targeted_reviewer_blind.csv | ✅ | ✅ | ✅ | ✅ |

All three files verified at the expected destination path. No discrepancies.
Note: `stance_targeted_master.csv` and `stance_targeted_reviewer_blind.csv`
share an identical SHA-256 hash (`0f6e6c4c...`) — they are byte-identical
copies of each other in the source project as well, not an artifact of
migration.

## E. Research documentation — expected at `docs/dataset/previous_research/`

| File | Source | Expected dest | Actual dest | Size/Hash match |
|---|---|---|---|---|
| data_inventory.csv | ✅ | ❌ not present | ✅ `docs/dataset/data_inventory.csv` | ✅ |
| protected_artifacts_baseline.json | ✅ | ❌ not present | ✅ `docs/dataset/protected_artifacts_baseline.json` | ✅ |
| MODEL_REGISTRY.md | ✅ | ❌ not present | ✅ `docs/dataset/MODEL_REGISTRY.md` | ✅ |
| INFERENCE_API.md | ✅ | ❌ not present | ✅ `docs/dataset/INFERENCE_API.md` | ✅ |

**Discrepancy:** All four Group E files were found directly under
`docs/dataset/`, not under `docs/dataset/previous_research/` as specified in
the migration plan. The `previous_research/` subfolder does not currently
exist under `docs/dataset/`. Content is fully intact and verified
byte-identical at the location where the files actually are — this is a
**path placement issue only**, not a data-loss or corruption issue. No file
was moved during this audit, per the read-only/no-move restriction; a
decision on whether to relocate these four files into a `previous_research/`
subfolder is left to a future, explicitly-requested action.

## CSV and dataset integrity checks

| File | Rows (excl. header) | Columns | Readable |
|---|---|---|---|
| Open Government Consultation Data 2017-18 Get Involved Questionnaire.csv | 8,213 | 98 | ✅ (latin-1 fallback; file is not strict UTF-8 in source either — pre-existing, not a migration artifact) |
| ap2016-18_individual_comments.csv | 160 | 19 | ✅ (latin-1 fallback, same pre-existing condition) |
| ConsultationData2017Engagement_Donnéesdesconsultations2017engagements.csv | 5,169 | 63 | ✅ (latin-1 fallback, same pre-existing condition) |
| unique_texts.csv | 10,043 | 8 | ✅ UTF-8 |
| corpus_entries.csv | 10,108 | 12 | ✅ UTF-8 |
| unique_texts_labeled.csv | 10,043 | 9 | ✅ UTF-8 |
| reconciliation.csv | 3 | 7 | ✅ UTF-8 |
| consolidated_stance_dataset.csv | 600 | 6 | ✅ UTF-8 |
| consolidated_stance_dataset_corrected.csv | 600 | 6 | ✅ UTF-8 |
| stance_human_gold_400_provisional.csv | 400 | 15 | ✅ UTF-8 |
| stance_targeted_master.csv | 134 | 8 | ✅ UTF-8 |
| stance_targeted_reviewer_blind.csv | 134 | 8 | ✅ UTF-8 |
| data_inventory.csv | 3 | 21 | ✅ UTF-8 |

Non-CSV files (`corpus_manifest.json`, `sampling_manifest.json`,
`protected_artifacts_baseline.json`, `MODEL_REGISTRY.md`, `INFERENCE_API.md`)
were verified by hash only, as row/column counts do not apply.

**Number of unique texts in `unique_texts.csv`:** 10,043 (one row per
`unique_id`).

**Annotation record counts:**
- `consolidated_stance_dataset.csv` / `consolidated_stance_dataset_corrected.csv`: 600 records each.
- `stance_human_gold_400_provisional.csv`: 400 records.
- `stance_targeted_master.csv` / `stance_targeted_reviewer_blind.csv`: 134 records each.

For the three source raw CSVs (Group A), the UTF-8 decode fallback to
latin-1 reflects the original file encoding as produced by the source
export tool (French-language headers with accented characters outside
strict UTF-8); this condition is identical in both the source and
destination copies and was not introduced by the migration.

## Restrictions honored

- No source or destination file content was modified.
- No files were deleted, moved, or overwritten.
- No dependencies were installed (verification used Python 3.13 standard
  library only, invoked with `-I` isolated mode).
- No `git add`, `commit`, or `push` was run.
- The only file written during this audit is this report.

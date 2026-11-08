# Data Ingestion Guide

Covers bulk CSV comment ingestion. For the single-document upload +
section extraction path, see `docs/backend/API_DOCUMENTATION.md`
(`POST /policies/{id}/documents`) and `docs/architecture/DATA_FLOW.md`.
For importing a finalized human annotation export specifically, see
[`ANNOTATION_IMPORT_SPEC.md`](ANNOTATION_IMPORT_SPEC.md).

## Bulk comment import

```
POST /policies/{policy_id}/comments/bulk-import
  multipart/form-data, field "file": a CSV
```

### Required CSV columns

| Column | Required | Notes |
|---|---|---|
| `original_text` | Yes | Rejected if blank/whitespace-only. |
| `source_dataset` | Yes | Identifies which external source this row came from. |
| `source_record_id` | Yes | The row's stable ID within that source — this is the idempotency key (see below), not the dedup key. |
| `language` | No | Defaults to `"unknown"`. |
| `policy_section_id` | No | Must belong to the target policy if given. |

A row missing any required column is recorded as a row-level error (see
"Error reports" below) — it does **not** abort the rest of the file.

### Two distinct kinds of "duplicate," handled differently

1. **Idempotent re-import** — the exact same `(policy_id, source_dataset,
   source_record_id)` already exists. The row is **skipped**
   (`skipped_already_imported_count`), not re-created and not
   multiplicity-bumped. This is what makes re-running an import after a
   network failure or a scheduler retry safe.
2. **Genuine duplicate text from a different real source record** — a
   *different* `source_record_id` whose text happens to normalize to the
   same hash as an existing comment. The existing comment's
   `multiplicity` is incremented (`incremented_count`) — this mirrors the
   canonical corpus's own `multiplicity` concept
   (`data/processed/canonical_corpus/unique_texts.csv`) and the single-
   comment submission endpoint's existing behavior.

### Batch processing

Rows are committed in chunks (`batch_size`, default 500) rather than one
giant transaction — bounds memory and lock duration on large files.
Within a batch, each row is additionally wrapped in its own `SAVEPOINT`
(`db.begin_nested()`), so one row's unexpected database-level failure
rolls back only that row, never the rows around it.

### Import reports and error reports

Every import call returns, and permanently stores (as an `ImportRun`
row — see `DATABASE_SCHEMA.md`):

```json
{
  "import_run_id": 42,
  "total_rows": 1000,
  "created_count": 950,
  "incremented_count": 30,
  "skipped_already_imported_count": 15,
  "error_count": 5,
  "errors": [ { "row_number": 812, "message": "Missing or blank required column 'source_record_id'", "text_snippet": "..." } ]
}
```

Up to 200 individual errors are retained in full detail; `error_count`
always reports the true total even if it exceeds that cap, so a large
error count is never silently truncated without saying so.

**Logging discipline:** `text_snippet` in any error is capped at 80
characters — error reports (and any future logging built on them) never
include full comment text, consistent with this project's "avoid
exposing sensitive comment content unnecessarily" principle (see
`PRIVACY_AND_ACCESS_CONTROL.md`).

## Export

```
GET /policies/{policy_id}/comments/export
```

Returns a CSV of every comment for the policy, joined with its latest
stance prediction if one exists (blank columns if not — never a
fabricated placeholder). Read-only; never modifies anything.

## Access control

Both the bulk-import and export endpoints require the `researcher` role
(`backend/app/services/authz.py::require_role(Role.RESEARCHER)`) — see
`PRIVACY_AND_ACCESS_CONTROL.md` for what that currently means in
practice (no real authentication is wired in yet; every request is
treated as an admin by default in this development phase).

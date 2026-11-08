# Backend Database Schema

Implements the 11 entities from
[`../architecture/DATA_MODEL.md`](../architecture/DATA_MODEL.md) as
SQLAlchemy models (`backend/app/models/`). SQLite by default, portable to
PostgreSQL (see `SETUP_GUIDE.md`). No migrations are wired up yet
(Alembic is installed and available for a future phase) — tables are
created directly via `Base.metadata.create_all()` on startup.

## Tables

| Table | Model | Key points |
|---|---|---|
| `policy_documents` | `PolicyDocument` | Supports multiple policies — every downstream table scopes to a `policy_document_id`. |
| `policy_document_versions` | `PolicyDocumentVersion` | **Append-only.** Re-ingesting a document creates a new row (`version_number` + 1); `raw_text` is never edited after insert. |
| `policy_sections` | `PolicySection` | Scoped to a specific `policy_document_version_id` (not just the document), so re-ingestion never collides with a prior version's sections. Falls back to one "Whole document" row when no structure is found. |
| `comments` | `Comment` | `original_text` is **immutable**. `normalized_text` is a separate, derived column. Deduplicated via a hash-based unique constraint on `(policy_document_id, normalized_text_hash)` — an exact-duplicate submission increments `multiplicity` on the existing row instead of inserting a new one. |
| `comment_source_metadata` | `CommentSourceMetadata` | One-to-one with `comments`; preserves `source_dataset` + `source_record_id`. |
| `stance_predictions` | `StancePrediction` | `label` and `exclusion_code` are mutually exclusive (DB-level `CHECK` constraint). `source` (`human`/`model`) is mandatory; `source='model'` requires a non-null `model_version_id` (also a `CHECK` constraint — enforced by the database itself, not just application code). `pass_number` supports the repeat-annotation design. |
| `concern_groups` | `ConcernGroup` | Scoped to a `model_version_id` (one clustering run). `is_noise` represents HDBSCAN's `-1` label as a real, queryable group rather than an omission. |
| `group_memberships` | `GroupMembership` | `comment_id -> group_id`. Unique on `(comment_id, model_version_id)` — one group per comment per clustering run. **No column here references stance** — the independence principle is structural, not conventional. |
| `representative_comments` | `RepresentativeComment` | Unique on `(group_id, comment_id)`; `rank` + `similarity_score` per entry. |
| `summaries` | `Summary` | `method` defaults to `extractive`. `model_version_id` is required at the application layer when `method='abstractive'` (see `services/validation.py`'s comment on why this specific rule isn't a plain `CHECK` constraint). |
| `evidence_references` | `EvidenceReference` | Links a `Summary` to its supporting comment(s). Unique on `(summary_id, comment_id)`. **A `Summary` with zero rows here is invalid** — checked by `services/validation.py::check_traceability_integrity`, not by a DB constraint (SQL can't easily express "at least one child row must exist" without a trigger). |
| `model_versions` | `ModelVersion` | Append-only record of every ML component version referenced by the tables above — "Preserve historical processing versions." |

## Enforced constraints (not just convention)

- `ck_stance_label_xor_exclusion` — a `StancePrediction` can never have both
  `label` and `exclusion_code` set.
- `ck_model_prediction_has_version` — `source='model'` without a
  `model_version_id` is rejected by the database, not just discouraged.
- `uq_comment_dedup` — prevents duplicate comment rows per policy.
- `uq_one_group_per_comment_per_run` — a comment cannot belong to two
  groups within the same clustering run.
- `uq_evidence_once_per_summary` — a comment can't be cited twice as
  evidence for the same summary.

## Traceability (checked independently, not self-certified)

`services/validation.py::check_traceability_integrity(db)` re-derives,
from scratch, whether every `GroupMembership`, `RepresentativeComment`,
and `EvidenceReference` resolves to a real `Comment`, and whether every
`Summary` has at least one `EvidenceReference`. This mirrors
`ml/stance_classification/validate_splits.py`'s pattern of auditing a
pipeline's output independently rather than trusting its own manifest —
see `research/methodology/RESEARCH_QUESTIONS_AND_HYPOTHESES.md` RQ4.

## Why SQLite now, PostgreSQL later

SQLite requires no separate server process — appropriate for local,
CPU-only, 8 GB RAM development with no paid infrastructure. Every model
uses SQLAlchemy's generic column types (`JSON`, `DateTime`, portable
`Enum` via `str_enum()` in `models/base.py`) specifically so the same
model code works unchanged against PostgreSQL once that becomes
necessary (e.g. for concurrent write access in a deployed setting).

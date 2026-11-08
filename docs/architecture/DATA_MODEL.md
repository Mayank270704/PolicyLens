# PolicyLens — Data Model and Traceability Design

Companion to [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md). Defines
concrete schemas for every entity named there. **Design document** — the
entities marked "implemented today" exist as CSV/JSON files under
`scripts/annotation/schema.py`'s conventions; everything else is proposed.

## Core traceability principle

> Grouping and summarization must never destroy or overwrite original
> comments.

This is enforced today by `scripts/annotation/validate.py`'s
`IMMUTABLE_FIELD_CHANGED` check (comment text/metadata compared against an
original backup on every validation run) and by
`ml/stance_classification/dataset_prep.py`'s `normalize_text()`, which
always writes to a **new** `normalized_text` field rather than overwriting
`comment_text`. Every entity below follows the same rule: any derived or
processed value lives in its own field or its own linked record, never in
place of the source.

## Entities

### Comment — *implemented today*

The permanent, immutable record of one public comment. Exact mirror of
`data/processed/canonical_corpus/unique_texts.csv` plus the annotation
layer's additions.

| Field | Type | Mutable? | Notes |
|---|---|---|---|
| `comment_id` (today: `unique_id`, re-encoded as `PL-NNNNNN` in annotation files) | string | No | Stable forever — see `SINGLE_ANNOTATOR_PROTOCOL.md` section 6. |
| `original_text` (today: `comment_text`) | string | **Never** | Verbatim source text. |
| `source_dataset` | string | No | Which ingestion source. |
| `source_record_id` | string | No | Row/record identity within that source. |
| `language` | string | No | As detected/declared at ingestion. |
| `multiplicity` | int | No | Count of duplicate raw entries collapsed into this unique text (precedent: `unique_texts.csv`'s own `multiplicity` column). |
| `normalized_text` | string | Yes (recomputed, never hand-edited) | Modeling-only derived field — see `dataset_prep.py`. |
| `policy_context`, `policy_section` | string | Yes (recomputed as retrieval improves) | See `SYSTEM_ARCHITECTURE.md` component 5. |

### StanceAnnotation — *partially implemented (human path only)*

| Field | Type | Notes |
|---|---|---|
| `comment_id` | string | FK to Comment. |
| `label` | enum(`Support`,`Oppose`,`Neutral`,`Unclear`) | Nullable if excluded. |
| `exclusion_code` | enum(`SPAM`,`OFF_TOPIC`,`TOO_SHORT_NONSUBSTANTIVE`,`UNINTELLIGIBLE`) | Nullable if labeled. Mutually exclusive with `label` — enforced today by `validate.py`'s `LABEL_AND_EXCLUSION_SET` check. |
| `confidence` | enum(`1`,`2`,`3`) | See `SINGLE_ANNOTATOR_PROTOCOL.md` section 6.2. |
| `notes` | string | Required for every `Unclear` label. |
| **`source`** | enum(`human`,`model`) | **Critical field, not present in today's flat CSV schema but required for any future production system** — once a trained classifier exists, its predictions must be schema-distinguishable from human annotations, never merged into one undifferentiated label column. |
| `annotator_or_model_id` | string | Which human (today: the single project-owner annotator) or which model/version produced this. |
| `model_version` | string, nullable | Required when `source = model`; references a specific trained-model artifact (hash-recorded, per `ml/stance_classification/dataset_prep.py`'s manifest pattern). |
| `created_at` | timestamp | |
| `pass_number` | int | `1` or `2`, for the 38-item repeat subset's intra-annotator check; absent/`1` for all other items. |

**Today's implementation note:** `scripts/annotation/schema.py`'s flat CSV
(`annotator_label`, `exclusion_code`, `annotation_confidence`,
`annotation_notes`) is the `source = human` case of this entity, written
before this more general model existed. A future database migration
should add `source` and `model_version` rather than requiring a second,
parallel table — the CSV's columns map directly onto this entity's fields
one-to-one except for those two.

### ConcernGroup / CommentGroupMembership — *proposed*

| Field | Type | Notes |
|---|---|---|
| `group_id` | string | |
| `method` | enum(`hdbscan`,`kmeans`) | Per `SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`. |
| `hyperparameters` | JSON | Full config for reproducibility. |
| `embedding_model` | string | e.g. `sentence-transformers/all-MiniLM-L6-v2`. |
| `created_at` | timestamp | |
| `size`, `noise` | int, bool | `noise=true` for HDBSCAN's `-1` label — see architecture doc's noise-handling note. |

`CommentGroupMembership(comment_id, group_id)` — many comments to one
group (baseline design); **never derived from or joined against
`StanceAnnotation` at creation time** — this is the schema-level
enforcement of the independence principle.

### RepresentativeComment — *proposed*

`RepresentativeComment(group_id, comment_id, rank, similarity_score)` —
3–5 rows per group, per `SYSTEM_ARCHITECTURE.md` component 8.

### Summary — *proposed*

| Field | Type | Notes |
|---|---|---|
| `group_id` | string | |
| `text` | string | |
| `method` | enum(`extractive`,`abstractive`) | Defaults to `extractive` — see architecture doc component 9's scope note. |
| `evidence_comment_ids` | list[string] | **Mandatory, non-empty.** A summary with no evidence is an invalid record, not a degenerate case to silently allow. |
| `model_version` | string, nullable | Required when `method = abstractive`. |
| `created_at` | timestamp | |

### PolicyDocument / PolicySection — *proposed*

`PolicyDocument(policy_id, title, jurisdiction, source_url, ingested_at,
raw_text_ref)`; `PolicySection(policy_id, section_id, section_label,
section_text)`. A policy with no derivable section structure gets exactly
one `PolicySection` representing the whole document — the schema-level
accommodation for the current corpus's real situation (no formal
clause-numbered document; see `SINGLE_ANNOTATOR_PROTOCOL.md` section 5).

### PolicyReport — *proposed*

`PolicyReport(policy_id, generated_at, stance_distribution,
exclusion_distribution, concern_group_refs: [group_id], completeness_flags)`
— `completeness_flags` records which upstream components had fully versus
partially available data at generation time (per architecture doc
component 10's error-handling requirement).

### AnnotationProvenance — *cross-cutting, partially implemented*

Not a single table so much as a guarantee threaded through
`StanceAnnotation` (`source`, `annotator_or_model_id`, `pass_number`) plus
two project-level artifacts that already exist:

- `data/annotations/new_experiment/audit_log.csv` — every overwrite of a
  previously-set label, with old/new values and a timestamp (implemented
  today, `scripts/annotation/state.py`).
- `data/annotations/new_experiment/repeat_annotation_plan.json` +
  `repeat_consistency_report.json` — the intra-annotator reliability
  record for the hidden repeat subset (implemented today).

A future database schema should preserve both as first-class, queryable
tables (`AnnotationAuditLog`, `ReliabilityCheck`) rather than flattening
them away during migration — provenance that can't be queried is
provenance that won't get checked.

## Traceability guarantees (what must always be true)

1. Every `StanceAnnotation.comment_id` resolves to a real `Comment`.
2. Every `CommentGroupMembership.comment_id` resolves to a real `Comment`,
   and every `.group_id` to a real `ConcernGroup`.
3. Every `Summary.evidence_comment_ids` entry resolves to a real `Comment`
   that is also a `RepresentativeComment` of that summary's `group_id`.
4. Every `PolicyReport.concern_group_refs` entry resolves to a real
   `ConcernGroup`.
5. No `Comment.original_text` value ever differs from its value at
   ingestion time, for the lifetime of the record.
6. A `StanceAnnotation` with `source = model` always has a non-null
   `model_version`; a `Summary` with `method = abstractive` always has a
   non-null `model_version`. Nothing claims to be machine-generated
   without saying which machine.

Guarantee 5 is enforced today (`validate.py`). Guarantees 1–4 and 6 are
proposed checks for the future database layer, directly analogous to
`ml/stance_classification/validate_splits.py`'s independent,
after-the-fact re-validation pattern — **validated by a separate process
from whatever wrote the data, not self-certified.**

## Why this isn't over-engineered

Every entity above corresponds to a real pipeline stage named in
`SYSTEM_ARCHITECTURE.md`, and every field exists to answer a traceability
or provenance question this project has already had to answer concretely
for the annotation subsystem (human vs. model, which pass, which
exclusion reason, which original value). Nothing here introduces a new
category of entity beyond what the 14-component architecture already
requires.

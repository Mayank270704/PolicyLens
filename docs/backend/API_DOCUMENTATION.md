# Backend API Documentation

**Live, interactive, auto-generated reference:** run the server
(`uvicorn backend.app.main:app --reload`) and visit `/docs` (Swagger UI)
or `/redoc`. This document is a static, readable overview for when the
server isn't running.

## Conventions

- **Pagination:** any list endpoint accepts `?page=1&page_size=25`
  (`page_size` max 200) and returns
  `{"items": [...], "total": N, "page": N, "page_size": N, "total_pages": N}`.
- **Errors:** every error response has the shape
  `{"error": {"code": "<http status>", "message": "..."}}`; validation
  errors (422) additionally include a `"details"` array with per-field
  messages.
- **No endpoint here fabricates a stance prediction, concern group, or
  summary.** Endpoints that retrieve these return exactly what's in the
  database — if nothing has been predicted/clustered/summarized yet, the
  response correctly reflects that (empty list, or `completeness_flags`
  on the report endpoint), per the project's standing restriction against
  fabricating model output.

## Endpoints

### Policy documents

| Method & path | Purpose |
|---|---|
| `POST /policies` | Create a policy document record. |
| `GET /policies` | List policies (paginated). |
| `GET /policies/{policy_id}` | Retrieve one policy. |
| `POST /policies/{policy_id}/documents` | Upload/ingest a file (`.txt`/`.html`/`.htm`/`.pdf`, ≤20 MB) — creates a new, versioned `PolicyDocumentVersion`; never overwrites a prior one. |
| `GET /policies/{policy_id}/sections` | List identified sections (paginated). |
| `GET /policies/{policy_id}/sections/{section_id}` | Retrieve one section. |

### Comments

| Method & path | Purpose |
|---|---|
| `POST /policies/{policy_id}/comments` | Submit a comment. Exact-duplicate text (same policy) increments `multiplicity` on the existing comment rather than creating a new one. |
| `GET /policies/{policy_id}/comments` | List comments for a policy (paginated). |
| `GET /comments/{comment_id}` | Retrieve one comment. |
| `POST /comments/{comment_id}/validate` | Run the PII-flag heuristic + exclusion-code suggestion heuristic; updates and returns `validation_status`. **Flags for human review — never a certified anonymity or exclusion decision.** |

### Stance

| Method & path | Purpose |
|---|---|
| `GET /comments/{comment_id}/stance` | List all stance-prediction records for a comment (human and/or model, across passes/versions). Empty list if none exist yet — not an error. |

### Concern groups and summaries

| Method & path | Purpose |
|---|---|
| `GET /policies/{policy_id}/concern-groups` | List concern groups for a policy (paginated). |
| `GET /concern-groups/{group_id}` | Retrieve one group, including its representative comments. |
| `GET /concern-groups/{group_id}/summary` | List summaries for a group (most recent first). |

### Reports

| Method & path | Purpose |
|---|---|
| `GET /policies/{policy_id}/report` | Aggregate stance distribution, exclusion distribution, concern-group counts, and `completeness_flags` stating which upstream pipelines have produced anything yet. |

### Bulk data (see `docs/backend/DATA_INGESTION_GUIDE.md` / `ANNOTATION_IMPORT_SPEC.md`)

| Method & path | Purpose | Access |
|---|---|---|
| `POST /policies/{policy_id}/comments/bulk-import` | Import comments from a CSV file. | `researcher`+ |
| `GET /policies/{policy_id}/comments/export` | Export all comments (+ latest stance, if any) as CSV. | `researcher`+ |
| `POST /policies/{policy_id}/annotations/import` | Import a `finalize.py`-shaped finalized-annotation CSV. | `researcher`+ |
| `GET /policies/{policy_id}/import-runs` | List the audit log of every import attempt (paginated). | open |

### Retrieval (see `docs/backend/RETRIEVAL_ARCHITECTURE.md`)

| Method & path | Purpose |
|---|---|
| `GET /policies/{policy_id}/retrieve?query=...&top_k=5` | BM25 lexical retrieval over the policy's sections. Response always includes an `accuracy_disclaimer` — no retrieval accuracy is claimed. |

### Analytics (see `docs/backend/ANALYTICS_API.md`)

| Method & path | Purpose |
|---|---|
| `GET /policies/{policy_id}/analytics` | Descriptive analytics: sources, languages, timeline, data quality, and stance/concern-group figures each paired with an `*_available` flag distinguishing "not run yet" from "genuinely zero." |
| `GET /analytics/summary` | Cross-policy totals. |

### Health

| Method & path | Purpose |
|---|---|
| `GET /health` | Liveness check. |

## Input validation highlights

- `original_text` must be non-blank (whitespace-only is rejected, not
  silently accepted as an empty comment).
- File uploads are validated by extension and size **before** any
  processing or database write (`backend/app/documents/ingestion.py::validate_upload`).
- `policy_section_id` on comment submission is checked to actually belong
  to the stated `policy_id`.

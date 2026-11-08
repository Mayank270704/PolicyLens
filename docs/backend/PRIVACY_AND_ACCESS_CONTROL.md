# Privacy and Access Control

States plainly, for every control in this section, whether it is
**implemented**, **an interface only (not enforced everywhere)**, or
**requires deployment configuration** — per the explicit instruction to
document exactly this distinction.

## Role-based authorization

**Interface implemented; not yet backed by real authentication.**
`backend/app/services/authz.py` defines three roles (`public`,
`researcher`, `admin`) and a `require_role(minimum_role)` FastAPI
dependency factory. It is wired onto the three endpoints that expose raw
submission content or bulk data:

- `GET /policies/{id}/comments/export` (raw `original_text` for every comment)
- `POST /policies/{id}/comments/bulk-import`
- `POST /policies/{id}/annotations/import`

**Development-mode default:** `get_current_user()` currently returns a
hardcoded admin user for every request — there is no login, no token,
no user store. **This must be replaced with a real authentication check
before any deployment handling genuine public submissions.** Every other
endpoint (policy CRUD, comment submission/retrieval, stance/concern-group
retrieval, analytics, retrieval) has no role requirement at all in this
phase — not because they're unimportant, but because retrofitting access
control onto 20 endpoints without a real identity system to back it would
be security theater; the three endpoints gated now are the concrete
demonstration of the pattern, applied to the data most worth protecting
first.

## Secure file handling

**Implemented.** `documents/ingestion.py::validate_upload` checks
extension and size *before* any content is read into an extractor.
Uploaded file bytes are never written to a shared or predictable
filesystem path — extraction happens entirely in memory
(`io.BytesIO`/direct string decode), and the only persisted artifact is
the extracted text stored in the database. The original filename is
never used to construct a filesystem path (it's stored only as a
metadata string), so there is no path-traversal surface from a malicious
filename.

## Import audit logs

**Implemented.** Every bulk comment import and annotation import creates
an `ImportRun` row (`backend/app/models/import_log.py`) — append-only,
recording `source_label`, timing, per-outcome counts, and up to 200
detailed row-level errors (with `error_count` always reporting the true
total, never silently truncated). Queryable via
`GET /policies/{id}/import-runs`.

## Data retention configuration

**Interface implemented; no automated deletion.**
`RETENTION_POLICY_DAYS` (unset by default — indefinite retention) and
`services/retention.py::find_retention_candidates()` identify comments
older than the configured threshold. **This function only ever reads and
reports; it never deletes anything.** Deleting real submitted public
comments is a records-retention/legal decision this codebase deliberately
does not automate — an actual deletion operation, if ever built, should
be a separate, explicitly-invoked, individually-audited action, not a
side effect of a reporting query.

## PII flagging

**Implemented, explicitly bounded.** `services/privacy.py::scan_for_pii`
is a regex heuristic (email/phone/SSN-shaped patterns). Its own
`PiiScanResult.DISCLAIMER` states, verbatim: a clean scan does **not**
mean the text is anonymous. `POST /comments/{id}/validate` surfaces this
flag for human review; nothing in this codebase treats
`pii_flagged=False` as a certified anonymity guarantee.

## Restricted access to raw submissions

**Partially implemented.** The export endpoint (which returns every
comment's full `original_text`) requires the `researcher` role (see
above). Single-comment retrieval (`GET /comments/{id}`) and the list
endpoint (`GET /policies/{id}/comments`) also return `original_text` and
currently have **no** role requirement — flagged here as the concrete
next step if raw-text exposure needs tightening further than the bulk
endpoints alone, rather than silently left unstated.

## Separation of contact details from research records

**Implemented at the schema level.** `backend/app/models/contact.py`'s
`SubmitterContact` table is deliberately separate from `Comment` and
every research/export/analytics code path. No function in
`services/bulk_export.py`, `services/analytics.py`,
`services/retrieval.py`, or the annotation-import adapter references this
table — structurally, a research export built from
`Comment`/`StancePrediction`/`ConcernGroup` cannot leak a contact field
that was never selected or joined into it. No endpoint populates this
table yet (no live submission form collects contact info in this phase);
it exists so the separation is already decided and in place before it's
ever needed, not improvised later.

## Logging

**Implemented.** Comment text is never logged by default
(`LOG_COMMENT_TEXT=false`, see `docs/backend/SETUP_GUIDE.md`). Import
error reports cap any included text to an 80-character snippet
(`bulk_import.py::TEXT_SNIPPET_LEN`), never the full comment.

## Summary table

| Control | Status |
|---|---|
| Role-based authorization | Interface implemented; applied to 3 of ~23 endpoints; no real auth backend |
| Secure file handling | Implemented |
| Import audit logs | Implemented |
| Data retention configuration | Interface implemented; no automated deletion (by design) |
| PII flagging | Implemented, explicitly bounded (regex heuristic, not a guarantee) |
| Restricted access to raw submissions | Partial — export is gated, single/list retrieval is not yet |
| Separation of contact details | Implemented at the schema level; unused until a real intake form exists |
| Logging discipline | Implemented |

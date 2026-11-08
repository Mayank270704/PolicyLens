# Policy Document Retrieval Architecture

`backend/app/services/retrieval.py` implements section-level lexical
retrieval over an ingested policy document.

## Why BM25, implemented from scratch

Neither `rank_bm25` nor `whoosh` is installed in this environment, and
nothing new was installed to build this feature — BM25 (Okapi BM25,
`k1=1.5`, `b=0.75` — standard defaults) is a well-defined, compact enough
formula to implement directly against the standard library
(`backend/app/services/retrieval.py::BM25Index`). The index is rebuilt
per query from a policy's sections rather than persisted, since this
project's policy documents are small enough (a handful to a few dozen
sections) that rebuilding is fast and far simpler than maintaining a
persistent inverted index — see
`docs/experiments/HARDWARE_FEASIBILITY_REPORT.md`'s general principle of
not over-engineering for a workload that doesn't need it.

## What's evaluated / considered, and the result

| Approach | Status |
|---|---|
| **BM25 lexical retrieval** | Implemented — the primary method. |
| **Section-level retrieval** (not whole-document) | Implemented — `PolicySection` is the unit retrieved against, using the heuristic sections `documents/sections.py` identifies. |
| **Metadata filtering** | Implemented — results are scoped to one `policy_document_id` and one `policy_document_version_id` before scoring, never mixed across policies or stale versions. |
| **Policy and document version filtering** | Implemented — defaults to the latest version if none is specified; an explicit `version_id` query parameter can target an older version. |
| **Retrieval result provenance** | Implemented — every result carries `method`, `query`, `policy_document_id`, `policy_document_version_id`, and `retrieved_at`, so any later evaluation can be run against a logged result set, not just a live re-query. |

## Independence from stance classification

`retrieval.py` imports nothing from the stance models — enforced, not
just documented, and checked by a static test
(`tests/unit/test_retrieval.py::test_retrieval_never_imports_stance_models`,
which parses the module's AST and fails if any stance-model import ever
appears). A query returns relevant policy text; it has no concept of, and
never returns, any stance information.

## No retrieval accuracy is claimed

There is no labeled relevance-evaluation dataset for this corpus — one
would need an explicit annotation effort (which query/section pairs are
actually relevant), separate from the stance-annotation one already in
progress, and out of scope for this phase. Every API response therefore
carries an explicit `accuracy_disclaimer` field stating this, and the
scores returned are raw BM25 relevance scores, not calibrated
probabilities or an accuracy percentage. This is a hard rule, not a
hedge: **nothing in this codebase computes or displays a precision,
recall, or accuracy number for retrieval**, because no evaluation exists
to compute one from.

## Endpoint

```
GET /policies/{policy_id}/retrieve?query=...&top_k=5&version_id=(optional)
```

Returns up to `top_k` sections with `score > 0` (a zero/negative BM25
score means no query term matched at all, so it's excluded as a
non-result rather than returned as an irrelevant match).

# Analytics API Documentation

`backend/app/services/analytics.py` + `backend/app/routers/analytics.py`.

## The core design rule: unavailable vs. zero

Every stance- or concern-group-related figure is paired with an
`*_available: bool` flag.

- `stance_available: false` means **no `StancePrediction` rows exist for
  any comment in this policy at all** — the classification pipeline
  hasn't run yet. `stance_distribution` will be `{}` in this case, but
  that `{}` means "nothing to report," not "zero of every stance."
- `stance_available: true` with a `stance_distribution` that's missing a
  particular label (e.g. no `"Oppose"` key) means that label's count is
  genuinely zero among real predictions — a materially different,
  rarer, and more meaningful situation than the pipeline simply not
  having run.
- The identical distinction applies to `concern_groups_available` /
  `concern_group_count`.

**No stance distribution, exclusion distribution, or concern-group count
in this module is ever computed from anything other than real database
rows.** There is no synthetic/placeholder fallback path anywhere in
`services/analytics.py` — this was a hard, explicit project restriction
("do not calculate fabricated stance distributions") and is enforced by
the module simply never containing a code path that could produce one.

## Endpoints

### `GET /policies/{policy_id}/analytics`

```json
{
  "policy_document_id": 1,
  "total_comments": 1000,
  "comments_by_source": {"get_involved_questionnaire_2017_18": 600, "consultation_compilation_2017_18": 400},
  "language_distribution": {"English": 890, "French": 110},
  "submission_timeline": {"2026-01-01": 50, "2026-01-02": 75},
  "data_quality": {
    "pii_flagged_count": 3, "validated_count": 950, "flagged_for_review_count": 10,
    "pending_validation_count": 40, "duplicate_text_merge_count": 12, "max_multiplicity": 4
  },
  "stance_available": false,
  "stance_distribution": {},
  "exclusion_distribution": {},
  "pending_stance_count": 1000,
  "concern_groups_available": false,
  "concern_group_count": 0,
  "noise_comment_count": 0,
  "generated_at": "2026-11-08T12:00:00+00:00"
}
```

### `GET /analytics/summary`

Cross-policy totals: `total_comments`, `comments_by_policy` (a dict keyed
by policy title, including policies with zero comments), `total_policies`.

## What's covered vs. related endpoints elsewhere

| Analytics requirement | Where |
|---|---|
| Total comments | `analytics.total_comments`, and `analytics/summary.total_comments` across all policies |
| Comments by source | `analytics.comments_by_source` |
| Comments by policy | `analytics/summary.comments_by_policy` |
| Language distribution | `analytics.language_distribution` |
| Submission timelines | `analytics.submission_timeline` (daily bucket counts) |
| Data-quality statistics | `analytics.data_quality` |
| Stance distribution when genuine predictions exist | `analytics.stance_distribution` + `stance_available` |
| Concern-group statistics when genuine groups exist | `analytics.concern_group_count`, `noise_comment_count` + `concern_groups_available` |

The existing `GET /policies/{policy_id}/report` endpoint
(`docs/backend/API_DOCUMENTATION.md`) provides a narrower, report-focused
view of some of the same stance/exclusion data with its own
`completeness_flags` — the two endpoints overlap deliberately (a report
is a curated subset for presentation; analytics is the fuller descriptive
dataset), not accidentally duplicated.

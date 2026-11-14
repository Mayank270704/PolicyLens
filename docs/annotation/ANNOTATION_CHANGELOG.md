# Indian annotation methodology — change log

All entries are **PROPOSED — NOT ADOPTED** unless marked ADOPTED. Originals are never edited:
- `OLD:indian/reports/mygov_annotation_codebook_v1.md`
- `OLD:indian/reports/tweets_annotation_guidelines_v1.md`

## 2026-11-14 — MyGov codebook v1 → PROPOSED v2

| Change | Rationale | Decision |
|---|---|---|
| `Mixed` removed; mixed positions resolved by the commenter's framing, otherwise `Unclear / MIXED` | Matches the four-class project objective | D1 |
| Off-topic moved from `Neutral` to `exclusion_code = OFF_TOPIC` | Separates topic relevance from stance | D2 |
| New exclusion codes `NON_SUBSTANTIVE`, `ATTACHMENT_ONLY`, `UNREADABLE`, `WITHHELD_PRIVACY` | Takes comprehension and access failures out of `Unclear` | D2 |
| `Unclear` requires one of 6 `unclear_reason` values | Makes the residual class analysable | — |
| Language skill becomes `needs_review = LANGUAGE` (reassign), not `Unclear` | Labels must not depend on who reads the comment | — |
| New rules: constructive amendments, conditionals, sarcasm, distrust, missing context, ambiguous target, negation | These cases were missing in v1 | — |
| Added `confidence` (1–3) **and** a separate `needs_review` + reason | Borderline cases must be findable; review requests must not distort confidence | — |
| One item per normalised duplicate group; member IDs kept | Avoids duplicate annotation and split leakage | D3 |
| `sentiment` removed from the stance batch | Avoids anchoring and later misuse as stance | D4 |
| `evidence_span` replaced by a non-verbatim `rationale` | Privacy | — |
| Agreement reporting extended to per-class agreement and the Neutral/Unclear/OFF_TOPIC confusion | Overall kappa hides failure on rare classes | — |

## 2026-11-14 — Tweets

| Change | Rationale | Decision |
|---|---|---|
| New PROPOSED tweet **stance** guide v1. The v1 sentiment guidelines are kept, unchanged, for sentiment only. | No tweet stance methodology existed | D5 |
| Required `stance_target`; tweets about a person or party only are `OFF_TOPIC` for this task | Stance needs a policy, proposal, initiative or issue target | D5 |
| Sampling plan v2 PROPOSED: locked test unchanged; 13 leaking or duplicate train/dev rows replaced | Removes author, text and near-duplicate leakage | D7 (adopt v2 plan) |

## Pending decisions

D1–D5 are described in `INDIAN_STANCE_CODEBOOK_REVIEW.md`. In addition:
- **D6:** adopt v2 after the pilot;
- **D7:** adopt the v2 tweet plan;
- **D8:** what to do about the duplicate pair inside the locked test.

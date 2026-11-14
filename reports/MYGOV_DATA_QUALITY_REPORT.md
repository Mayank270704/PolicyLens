# MyGov data-quality report (v2)

**Status:** COMPLETE.
**Script:** `python -m ml.indian_stance.mygov_quality --out-dir data/processed/indian/mygov_quality_v2`.
**Outputs:** gitignored and IDs-only, in `data/processed/indian/mygov_quality_v2/`:
- `dedup_groups.csv` (541 rows)
- `truncation_candidates.csv` (98)
- `pii_review.csv` (23)
- `summary.json`
- `manifest.json`, with input and output SHA-256

No comment text and no personal value appears in any output or in this report.

> `mygov_quality_v1/` is **superseded**. It measured truncation on the whitespace-cleaned text, which gave 89/42 instead of 98/49. The 500-character cap applies to the raw submission, and cleaning shortened 133 texts by up to 28 characters, so v2 measures raw text. v1 is kept, not deleted.

## 1. Scope

- **One consultation:** the draft *Government Open Data Use License – India* (MyGov, 2016).
- **Coverage:** 550 unique comments out of the 1,132 the page displays (48.6%), from saved page indices 0–54 only. These are the **most recent half**, not a random sample.
- **Fields:** no submission dates (relative only) and no language field (script only).
- **Single-consultation limitation:** any model trained on this source learns stance toward *one* draft licence. Results cannot be claimed for Indian consultations, policies or comments in general. Cross-policy generalisation needs a second consultation, which does not exist locally.

## 2. Duplicates

| Check | Result |
|---|---|
| Raw records / unique comment IDs | 560 / 550. The 10 duplicate-ID records come from one duplicated saved page, and **all carry identical text**. |
| Distinct texts, exact | 542 |
| Normalised-text groups (NFKC, whitespace, lowercase) | **541**: 9 groups of 2 cover 18 comments; 1 of them differs only in whitespace or case |
| Agreement with the OLD `exact_text_duplicate_group` | Identical grouping |
| Representative rule | Numerically smallest comment ID in each group (deterministic) |

## 3. Possible truncation (500-character cap; raw text)

| Class | Comments | In the 541 candidate pool |
|---|---|---|
| At or above 490 characters | 98 | — |
| `LIKELY_TRUNCATED` (also no terminal punctuation) | **49** | 47 |
| `AT_LIMIT_COMPLETE_ENDING` | 49 | — |

The batch carries `possible_truncation`. The proposed codebook says: label from the visible text, and use `Unclear / TRUNCATED` only if the position is lost.

## 4. Possible personal information (23 flagged; values never reproduced)

| Proposed handling | Comments | Categories (comments) | Detected span in first 80% of text |
|---|---|---|---|
| `AUTO_REDACT` (typed placeholders: `[URL]`, `[PHONE]`, …) | 9 | url 8, phone-like 2 | 5 |
| `MANUAL_REVIEW` (sign-off / "on behalf of", which may carry a person's or organisation's name) | 14 | sign-off 14, email 2, url 3, phone-like 1 | 6 |

There were no Aadhaar-like, PAN-like or @mention matches. Recomputed flags agree with the recorded `any_flag` for 550/550 comments.

**Can redaction be done safely?**
- **Partly automatic.** Contact details and links can be replaced by typed placeholders, which keeps the fact that a link or number was given. Automatic redaction would remove at most 22.6% of an `AUTO_REDACT` comment's characters.
- **Sign-offs need a person.** Name detection is not reliable, so the 14 `MANUAL_REVIEW` comments are **withheld** from any annotator view until a data steward supplies reviewed text (`materialize_text.py --steward-redactions`).
- **Stance meaning is unverified.** Code can only show *where* spans sit: 11 flagged comments have a span in the body. Whether a redaction removes stance-bearing content must be confirmed by the steward. That is a human task.

## 5. Other annotation-relevant flags

- **Attachments:** 26 comments report an attachment, which was never saved; 6 of these have 10 words or fewer. Proposed exclusion code: `ATTACHMENT_ONLY`, when nothing else is readable.
- **Script:** Latin 525, Devanagari 14, mixed 1, other 1 (candidate pool). Devanagari items need a fluent annotator; the proposal is `needs_review = LANGUAGE`, not `Unclear`.
- **Length:** 1 to 101 words, median 52.

## 6. Is the 541-item pool usable for annotation?

**Methodologically yes:**
- one item per normalised-text group, with all member IDs recorded;
- 49 of the 50 OLD pilot comments are representatives (the 50th duplicates another item), so the pilot concept survives;
- flags for truncation, attachments, script and privacy handling are attached.

**Practically blocked.** The project's own rights audit records MyGov reuse and annotation permission as **not evidenced**, so the batch is metadata-only. See [INDIAN_DATA_PROVENANCE_AND_RIGHTS.md](INDIAN_DATA_PROVENANCE_AND_RIGHTS.md).

**Expected yield:** stance classes are unknown until annotation.
- **Off-topic comments:** the OLD codebook's exploratory clustering found off-topic groups. Under the proposed v2 codebook those become `OFF_TOPIC` exclusions, so the trainable pool will be smaller than 541.
- **Sample size:** about 541 items from one consultation is a pilot-scale dataset, and a credible four-class model will probably need more.

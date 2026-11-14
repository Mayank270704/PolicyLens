# PROPOSED Indian stance codebook v2 — MyGov (PROPOSED — NOT ADOPTED)

> **Status: PROPOSED — NOT ADOPTED.** The original `OLD:indian/reports/mygov_annotation_codebook_v1.md` is unchanged and remains the only existing codebook. This proposal needs the decisions D1–D6 in [INDIAN_STANCE_CODEBOOK_REVIEW.md](INDIAN_STANCE_CODEBOOK_REVIEW.md) and a pilot before use.
>
> **Machine-readable schema:** `ml/indian_stance/annotation_schema.py` (`indian_stance_annotation_schema_v2_PROPOSED`). The validator `ml/indian_stance/validate_annotations.py` enforces it.
>
> **Examples:** every example below is **SYNTHETIC**, written for this document. No real comment is quoted.

## 1. Stance target (unchanged from v1)

The author's position on the **draft Government Open Data Use License – India (2016)**, and on releasing government data under that open licence, including any clause the comment addresses. Batch field: `stance_target = GODL_INDIA_DRAFT_2016`.

**In scope:**
- the licence and its clauses;
- attribution;
- exemptions and restricted data;
- liability;
- commercial reuse and fees;
- formats, APIs and portals for data released under it;
- privacy and security of the data released.

**Out of scope (→ `OFF_TOPIC`):**
- government in general;
- other schemes (Digital India, Aadhaar, taxes, internet speed);
- services unrelated to data release.

## 2. Fields

| Field | Values | Rule |
|---|---|---|
| `exclusion_code` | `OFF_TOPIC`, `NON_SUBSTANTIVE`, `ATTACHMENT_ONLY`, `UNREADABLE`, `WITHHELD_PRIVACY` | Set **instead of** a stance when the item cannot carry a stance (§4). `WITHHELD_PRIVACY` is set by the data steward only. |
| `stance` | `Support`, `Oppose`, `Neutral`, `Unclear` | Exactly one of `stance` or `exclusion_code` is set. |
| `unclear_reason` | `MIXED`, `AMBIGUOUS_TARGET`, `CONDITIONAL_UNRESOLVED`, `MISSING_CONTEXT`, `TRUNCATED`, `SARCASM_UNRESOLVED` | Required when `stance = Unclear`; otherwise blank. |
| `confidence` | `1` low / borderline, `2` medium, `3` high | **How clear the decision is.** It is a property of the label, required for every annotated row. |
| `needs_review` | `yes` / `no` | **A workflow request**, independent of confidence. A confident label can still need review (e.g. a guideline gap). |
| `needs_review_reason` | `BORDERLINE`, `LANGUAGE`, `PRIVACY`, `GUIDELINE_GAP`, `OTHER` | Required when `needs_review = yes`. |
| `rationale` | Your own words, 3 or more words; **never copy names, emails or numbers** | Required for Oppose, Unclear, any exclusion, and `needs_review = yes`. |
| `clause_referenced` | Clause numbers (`2;5`), `general` or `none` | Unchanged from v1. `clause_numbers_detected` is an aid, not a label. |
| `concern_type` | The v1 closed set, minus `off_topic_other_policy` (now `OFF_TOPIC`) | Primary concern only. |
| `requested_action` | A verb phrase of up to 20 words, `none` or `unclear` | Unchanged from v1. |
| `annotator_id` | `annotator_A` / `annotator_B` | One annotator per sheet. |

**Removed from v1:**
- `Mixed` (decision D1);
- `sentiment` (D4);
- `evidence_span`, because of privacy; `rationale` replaces it.

## 3. Stance labels

| Label | Use when | Not this label when |
|---|---|---|
| **Support** | Endorses the draft licence or open release under it. This includes asking for **more or better openness**, or a **constructive amendment** (even one adding safeguards) that keeps the licence. | Generic praise of the government (→ Neutral or OFF_TOPIC) |
| **Oppose** | Rejects the licence or open release of government data. Argues it should be withdrawn or not adopted, or that some data must not be opened *as a reason against the licence*. | Criticism of wording plus a request to fix it (→ Support) |
| **Neutral** | On target, but no position: questions, information, procedural remarks, experience, suggestions that propose nothing evaluative. | Off-topic (→ `OFF_TOPIC`); no evaluable content (→ `NON_SUBSTANTIVE`) |
| **Unclear** | On target, contains an **identifiable** position, but its direction can't be resolved. Record one `unclear_reason`. | No position at all (→ Neutral); ambiguity of *wording* alone |

## 4. Exclusion codes (not stance classes)

| Code | Use when |
|---|---|
| `OFF_TOPIC` | No part of the comment is about the stance target (§1). A strong opinion on another subject is still OFF_TOPIC. If *part* is on target, label from that part and say so in `rationale`. |
| `NON_SUBSTANTIVE` | No evaluable content: greetings, "ok", "+1", bare agreement with content that is not available. |
| `ATTACHMENT_ONLY` | The content is in an attachment that was not saved, and the visible text carries no position. |
| `UNREADABLE` | Garbled or corrupted text, unreadable by anyone. If *you* can't read the language, use `needs_review = LANGUAGE` instead. |
| `WITHHELD_PRIVACY` | Steward only: text withheld pending privacy review. |

## 5. Decision order

1. **Readable and substantive?** If not: `UNREADABLE`, `ATTACHMENT_ONLY` or `NON_SUBSTANTIVE`. If you can't read the language: leave the labels blank and set `needs_review = yes, LANGUAGE`.
2. **About the target (§1)?** If no part is: `OFF_TOPIC`.
3. **Does it take a position on the target?**
   - No → **Neutral**.
   - Yes, and the direction is resolvable → **Support** or **Oppose** (rules R1–R6 below).
   - Yes, but the direction can't be resolved → **Unclear** with a reason.
4. **Set confidence.** Then set `needs_review`, separately.

## 6. Decision rules

| Rule | Situation | Label |
|---|---|---|
| R1 | Criticism of a clause **plus** a request to improve it, keeping the licence | Support |
| R2 | Both endorsement and rejection. The commenter's own framing gives an overall verdict, marks one side as minor, or dismisses one side. | The direction that framing gives. **Intensity of wording never decides it.** |
| R3 | Both, with no such signal from the commenter | Unclear / `MIXED` |
| R4 | Conditional, where the condition is a core objection to the draft as written | Oppose |
| R5 | Conditional, where the condition is minor or is already what the draft does | Its underlying direction |
| R6 | Conditional, where whether the condition is met is unknown | Unclear / `CONDITIONAL_UNRESOLVED` |
| R7 | Sarcasm whose intended direction is clear | Its intended direction |
| R8 | Sarcasm that can't be resolved | Unclear / `SARCASM_UNRESOLVED`, confidence 1 |
| R9 | Distrust ("they will misuse it") with no stated position on the licence | Neutral |
| R10 | Position depends on unseen content (a reply to, or a reference to, a missing comment or attachment) | Unclear / `MISSING_CONTEXT` |
| R11 | Position cut off by truncation | Unclear / `TRUNCATED`. If the visible text already gives a position, label it. |
| R12 | Unclear what the comment is about (licence vs. government in general) **and** it carries a position | Unclear / `AMBIGUOUS_TARGET` |
| R13 | Negation inside a description, clarification or fact | Not a stance cue by itself |

**SYNTHETIC examples:**

| SYNTHETIC comment | Label |
|---|---|
| "Clause 4's attribution wording is confusing; please simplify it so more people can reuse the data." | Support (R1) |
| "Opening ministry data like this is dangerous and the licence should be dropped." | Oppose |
| "Will datasets released earlier also fall under this licence?" | Neutral |
| "Good idea overall, though the liability clause needs work." | Support (R2: "overall") |
| "Reuse should be free, but releasing this data at all worries me — I can't decide." | Unclear / MIXED (R3) |
| "I'll support it only if personal data is fully excluded." (the draft already excludes it) | Support (R5) |
| "Fix the potholes on my road first." | `OFF_TOPIC` |
| "As I said in my earlier comment, agreed." | `NON_SUBSTANTIVE` |
| "Please see the attached document." | `ATTACHMENT_ONLY` |

## 7. Duplicates, privacy, truncation, language

- **Duplicates:** one item per normalised-text group (`member_comment_ids` lists every source ID). Label the item once.
- **Text and privacy:** text is shown only after a recorded rights and privacy clearance. Contact details appear as `[EMAIL]`, `[PHONE]`, `[URL]` or `[ID_NUMBER]`. Items needing manual redaction are withheld. Never type names or contact details into any field.
- **Truncation:** `possible_truncation = True` means the comment may be cut off at 500 characters (R11).
- **Language:** Devanagari, mixed and other scripts go to a fluent annotator. There is no machine translation.

## 8. Workflow and acceptance

1. **Pilot:** the 49 pilot representatives (`legacy_annotation_batch = pilot_50`). Two annotators work independently, without discussion and without model output.
2. **Agreement:** report Cohen's kappa for stance and exclusion together, per-class agreement, and confusion between Neutral, Unclear and `OFF_TOPIC`. Revise the codebook (logged in [ANNOTATION_CHANGELOG.md](ANNOTATION_CHANGELOG.md)) if overall kappa is below 0.60 or any class's agreement is poor.
3. **Main batch:** the remaining 492 items, then adjudication by a third person where possible.
4. **Ground truth:** only adjudicated or agreed labels are exported, as `label_source = human_adjudicated`. Blank templates are never annotations.

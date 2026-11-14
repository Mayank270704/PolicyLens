# PROPOSED tweet stance guide v1 — Indian politics tweets (PROPOSED — NOT ADOPTED)

> **Status: PROPOSED — NOT ADOPTED.** The existing `OLD:indian/reports/tweets_annotation_guidelines_v1.md` is a *sentiment* guide and is unchanged. Tweet **stance** annotation needs research decision **D5** (stance targets) before any annotation. All examples are **SYNTHETIC**.

## 1. Why this is a separate guide

MyGov comments answer one consultation, so there is one fixed target. Tweets have no shared target, the authors are not responding to a consultation, and many tweets are about people or parties rather than a policy. The MyGov codebook therefore does not transfer as-is.

## 2. Stance target (needs decision D5)

Proposed rule:
- Stance is judged toward **one specific policy, proposal, initiative or public issue** that the tweet names or clearly refers to.
- The annotator records it in **`stance_target`** as a short, normalised name (e.g. "farm laws", "new metro line", "fuel price policy").
- A tweet about a person or party **only**, with no policy, proposal or issue, is `OFF_TOPIC` for this task. The rationale should say "person/party only".
- If a tweet has several policy targets, label the **main** one and note the others in `rationale`.

**Open questions for D5:**
- a fixed target list or free text normalised later;
- whether "issues" (e.g. inflation) count;
- the minimum number of examples per target before it is usable.

## 3. Labels and fields

Same schema as the MyGov v2 proposal (`ml/indian_stance/annotation_schema.py`): `stance` (4 classes), `exclusion_code`, `unclear_reason`, `confidence`, `needs_review` + reason, `rationale`, `annotator_id`. Tweets also have:
- **`stance_target`**, required whenever a stance is given;
- **`sarcasm_or_irony`** (`yes` / `no` / `unsure`).

## 4. Tweet-specific rules

| Situation | Label |
|---|---|
| Praise or insult of a leader with no policy referenced | `OFF_TOPIC` (person/party only) |
| A news headline or fact with no evaluative wording | Neutral |
| A quote or retweet with no added comment by the author | Neutral, or Unclear / `MISSING_CONTEXT` if the author's stance can't be told |
| A reply whose meaning depends on the unseen parent tweet | Unclear / `MISSING_CONTEXT` |
| Hashtag-only stance ("#RepealX") | That direction if the hashtag is unambiguous; otherwise Unclear / `AMBIGUOUS_TARGET` |
| Sarcasm | As MyGov R7/R8, and also set `sarcasm_or_irony` |
| Romanised Hindi or Hindi you can't read fluently | Blank labels, `needs_review = yes, LANGUAGE` |
| Likes or retweets | Never evidence; ignore them |

**SYNTHETIC examples:**

| SYNTHETIC tweet | stance_target | Label |
|---|---|---|
| "The new metro line will transform daily travel here — great decision" | new metro line | Support |
| "Scrap these farm laws now #FarmersProtest" | farm laws | Oppose |
| "When does the new fuel tax apply?" | fuel tax | Neutral |
| "What a leader, love him" | — | `OFF_TOPIC` |
| "Oh great, another 'reform' that fixes everything" (target unclear) | reform (unclear) | Unclear / `SARCASM_UNRESOLVED` |

## 5. Batch and splits

- **Batch:** `data/annotations/indian/tweets_batch_v2/` holds 1,500 items from the PROPOSED v2 sampling plan (pilot 200 → main 1,000 → locked test 300). The locked-test rows are unchanged from the original plan, and no author or masked text crosses the boundary.
- **Locked test:** annotate it last. **Never** use it for guideline revision or model selection.
- **Weak predictions:** the Sentiment140-derived predictions are not shown to annotators and are never stance labels.

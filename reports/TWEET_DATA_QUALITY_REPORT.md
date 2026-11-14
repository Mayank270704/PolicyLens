# Indian politics tweets — data-quality report

**Status:** COMPLETE.
**Script:** `python -m ml.indian_stance.tweets_split --out-dir data/processed/indian/tweets_split_v2`.
**Outputs:** gitignored, IDs and hashes only, in `data/processed/indian/tweets_split_v2/` (`summary.json`, `manifest.json`).

No tweet text, handle or URL appears here.

> `tweets_split_v2_run1_superseded/` is a run whose final console print failed; its `summary.json` stored one flag as a string. It is kept and replaced by the next run.

## 1. Source

- **What it is:** social-media posts collected for an "Indian politics" topic, **not consultation submissions**. It is kept separate from MyGov.
- **Rows:** 50,000 tweets after repairing one split-line record (50,001 raw CSV records).
- **Dates:** 2022-10-15 to 2023-03-29. Per month, 7,036–11,457 tweets.
- **Authors:** 35,109 pseudonymous author IDs; 6,341 authors have 2 or more tweets.
- **Missing fields:** there are no real tweet IDs, so deletion requests can't be traced. No licence or terms file exists locally.
- **Language:** script only. Latin 49,802, mixed 198. English and romanised Hindi (Hinglish) **cannot be distinguished** without a language-identification tool, which is not installed.
- **Labels:** no stance or sentiment labels. Likes and retweets are engagement counts, not labels.

## 2. Duplicates

| Definition | Distinct texts | Groups with 2+ tweets | Tweets in those groups |
|---|---|---|---|
| Exact | 49,569 | 247 (the OLD `exact_text_duplicate_group`) | 717 |
| Whitespace + case | 49,530 | — | — |
| @mentions and URLs masked, NFKC, whitespace, case | **48,163** | **823** | **2,660** (largest group 53) |

The masked definition matters for leakage: replies or retweets that differ only in the addressed user or the link collapse to one text. The OLD sampling rule deduplicated **exact** groups only. As a result, the original 1,500-row plan has 9 rows sharing a masked group, 2 of them across the locked-test boundary. See [TWEET_SPLIT_LEAKAGE_REVIEW.md](TWEET_SPLIT_LEAKAGE_REVIEW.md).

## 3. The 1,500-row sampling plan

Re-implemented from the OLD algorithm (seed 42): one tweet per exact group, at most 2 per author, 250 per month. The result **reproduces the existing plan exactly**: same IDs, order, splits (300 locked test, 1,200 train/dev) and batches (200 pilot, 1,000 main, 300 test).

**Script mix in the plan:** Latin 1,496, mixed 4.

**Weak predictions are quarantined:** the 50,000 Sentiment140-derived binary *sentiment* predictions are marked `NOT_ground_truth`. They are never stance labels, are not in any new batch, and are rejected by the training loader.

## 4. What the existing annotation design does not cover

- **No stance task exists yet.** The OLD guidelines are **sentiment-only** and explicitly exclude stance. Their 200-row pilot templates have a `sentiment` column and no stance column; both are blank.
- **No stance target is defined.** Political tweets have no single policy target. Stance needs a target, and many tweets concern people or parties rather than a policy. This is a research decision; see `docs/annotation/PROPOSED_TWEET_STANCE_GUIDE_v1.md`.

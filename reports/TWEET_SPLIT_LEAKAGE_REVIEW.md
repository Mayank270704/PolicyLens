# Tweet split leakage review and v2 proposal

**Status:** COMPLETE. The v2 plan is **PROPOSED — NOT ADOPTED**, and the original plan is unchanged.

**Script:** `ml/indian_stance/tweets_split.py`.

**Outputs** in `data/processed/indian/tweets_split_v2/` (gitignored):
- `sampling_plan_1500_v2_PROPOSED.csv` (IDs, splits, batches, `v2_status`, masked-text group hash)
- `v2_changes.csv`
- `summary.json`
- `manifest.json`

**Leakage definitions:** a train/dev tweet *leaks* into the locked test set if any of the following holds:
- it shares a pseudonymous **author**;
- it shares a **masked-normalised text** (mentions/URLs masked, NFKC, whitespace, case);
- it is a **near-duplicate**: token-set Jaccard ≥ 0.8 on masked text.

## 1. Original plan (OLD `sampling_plan_1500.csv`)

| Check | Result |
|---|---|
| Authors in both locked test and train/dev | **6** |
| Masked-text groups in both | **2** |
| Near-duplicate pairs (test vs train/dev) | **6** |
| Train/dev rows affected (by any of the three) | **12** |
| Rows sharing a masked group anywhere in the plan | 9 |

The audit's figures (6 authors, 2 normalised texts) are confirmed. The near-duplicate check adds cases the audit did not test.

## 2. v2 proposal: locked test unchanged, train/dev repaired

**Rules:**
- The 300 locked-test rows are kept **as they are**: same IDs, verified identical.
- A train/dev row is removed if it leaks into the locked test (any of the three definitions), or repeats a masked group already in the plan.
- Each removed row is replaced by the next eligible tweet **from the same month, in the original seeded order**, under the original rules: at most 2 per author, one per exact group. The replacement also must not share a masked group, an author, or near-duplicate text with the locked test.
- The replacement **inherits the removed row's batch** (pilot_200 or main).

| | Original | v2 PROPOSED |
|---|---|---|
| Rows / split / batch counts | 1,500; 300 / 1,200; 200 / 1,000 / 300 | identical |
| Per month | 250 each | 250 each |
| Script (Latin / mixed) | 1,496 / 4 | 1,496 / 4 |
| Authors / masked groups / near-dup pairs crossing | 6 / 2 / 6 | **0 / 0 / 0** |
| Rows replaced | — | **13** (12 leaking + 1 within-plan masked duplicate); 0 dropped without replacement |
| Reasons | — | author in locked test 6; near-duplicate of locked test 3; masked group plus near-duplicate 3; within-plan masked duplicate 1 |
| Pilot rows changed | — | **3 of 200**: the OLD blank pilot templates would need regenerating if v2 is adopted |

## 3. Remaining issues (decisions, not fixes)

1. **A duplicate inside the locked test.** Two locked-test tweets (row IDs 6418 and 6545) share one masked text. This is not train/test leakage, but it double-counts one text in evaluation. Fixing it would **change locked evaluation data**, which needs your explicit decision. It is left unchanged.
2. **Wider corpus.** Locked-test authors have **728** other tweets outside the plan (128 of the 300 test tweets have such an author). 83 outside tweets share a masked group with 14 test tweets. Any future training on tweets *outside* this plan must exclude those authors and groups. The training pipeline's group-aware checks enforce this when the group columns are supplied.
3. **Adoption.** v2 replaces the original split only if you adopt it. The new annotation batch is built from v2 and labelled PROPOSED.

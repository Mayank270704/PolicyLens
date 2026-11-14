# Indian stance model — training plan

**Status:** the framework is implemented and tested. **No Indian stance model has been trained**, and no metric exists. Training is blocked by design until adjudicated human stance labels exist.

## 1. What is executable now and what waits

| Component | Status | Notes |
|---|---|---|
| Source-aware loader with strict label validation (`ml/indian_stance/data_loader.py`) | **Executable** | Refuses everything below |
| Group-aware split and leakage checker (`splits.py`) | **Executable** | Tested on synthetic data |
| Baseline training with validation-only selection (`train.py`) | **Executable, refuses** | No eligible label file exists. On the real blank MyGov sheet and on the weak Sentiment140 predictions it exits with `[REFUSED]`. |
| Single-use test evaluation (`evaluate.py`) | Executable after a training run | — |
| Configuration (`configs/indian_stance/baseline_v1.json`) | Fixed | — |
| **A trained model and metrics** | **Awaits annotation** | Needs cleared text, a pilot, and adjudicated labels |

## 2. Input: the adjudicated label file

One CSV per source, one row per annotation item:

| Column | Rule |
|---|---|
| `item_id` | Unique; the batch item ID (`MYG2-…`, `TWT2-…`) |
| `source` | `mygov` or `tweets`. **`civis`, `lok_sabha`, `sentiment140` and other sentiment sets are refused.** |
| `text` | The redacted display text used by annotators |
| `stance` | `Support` / `Oppose` / `Neutral` / `Unclear`. Blank values, `Mixed`, `positive`, `negative`, `0`, `4` and similar are refused. Rows with an exclusion code are left out of the file. |
| `label_source` | Exactly `human_adjudicated`. Anything containing weak, pseudo, model, prediction, AI, heuristic, sentiment, auto, synthetic or silver is refused. |
| `adjudication_status` | `adjudicated` or `agreed` |
| `annotator_ids` | At least 2 distinct IDs, separated by `;` |
| `text_group_id` | MyGov: normalised-text hash. Tweets: `masked_text_group`. Required. |
| `author_group_id` | Tweets: `author_pseudo_id`. MyGov: blank. |
| `split` | `locked_test` for the tweets' locked test rows; otherwise blank |

**Merging sources:** mixing MyGov and tweets is refused unless `--allow-multi-source` is given with a written `--merge-justification`. Validation and test metrics are then also reported **per source**.

**Recommended order:** MyGov alone first; tweets alone after decision D5. Merge only with a documented research reason.

## 3. Splits and leakage control

- **Groups:** rows sharing `item_id`, `text_group_id` or `author_group_id` are joined into one component, and a component goes to exactly one split.
- **Stratification:** by each component's majority label; seeded.
- **Proportions:** MyGov uses 70/15/15. Tweets honour the pre-registered locked test as-is. A component spanning locked and non-locked rows is **refused**; the locked rows are never moved.
- **Leakage check:** before training, the checker fails on any shared item, text group, author or normalised text across splits, or any test-vs-rest near-duplicate (token Jaccard ≥ 0.8).
- **Class floor:** at least 5 training examples per class (`min_per_class_train`), and every class present in validation. Otherwise training is refused.

## 4. Models

| Name | Features | Classifier | Grid |
|---|---|---|---|
| `tfidf_word_logreg` | Word 1–2-gram TF-IDF, sublinear | Logistic Regression | C ∈ {0.3, 1, 3, 10}; min_df ∈ {1, 2}; class_weight ∈ {none, balanced} |
| `tfidf_wordchar_linearsvc` | Word 1–2-gram + char_wb 2–5-gram TF-IDF | LinearSVC | C ∈ {0.1, 0.3, 1, 3}; min_df ∈ {1, 2}; class_weight ∈ {none, balanced} |

- **Tokenisation:** **no stop-word list** (keeps negations; lesson from the Canadian Experiment 3). The token pattern keeps Devanagari words whole, because vowel signs are not `\w` in Python's regex.
- **Class weighting:** `balanced` is *in the grid*. It is chosen only if it wins on validation macro-F1, which is justified because Oppose was a minority class in every earlier dataset.
- **Fitting:** vectorisers are fitted on training data only, inside the pipeline.

## 5. Selection and evaluation

1. **Selection:** by **validation macro-F1** only; ties keep the earlier, simpler configuration. Each run records validation macro-F1 per source.
2. **Test:** `evaluate.py` runs **once** per run. It refuses a second evaluation, a changed data file, or a model whose hash doesn't match.
3. **Reported metrics:** per-class precision, recall and F1; macro-F1; weighted-F1; accuracy; the confusion matrix (fixed label order); the classification report; and the same breakdown per source.
4. **Error analysis:** `error_analysis.csv` holds item ID, source, true and predicted labels, and unclear reason. It contains no text.
5. **Reporting:** no metric is reported before a real run exists. Every run directory holds `run_manifest.json` with:
   - the SHA-256 of the data, config and model;
   - the git commit;
   - the seed (20261114);
   - label counts per split;
   - the leakage-check result;
   - the package versions.

## 6. Commands (once labels exist)

```
python -m ml.indian_stance.train --data <mygov_adjudicated.csv> --config configs/indian_stance/baseline_v1.json \
    --out-dir data/processed/indian/runs/mygov_baseline_v1
python -m ml.indian_stance.evaluate --run-dir data/processed/indian/runs/mygov_baseline_v1 --data <mygov_adjudicated.csv>
```

## 7. Feasibility and known limits

- **MyGov:** at most 541 items, fewer once `OFF_TOPIC` and other exclusions are removed, all from one consultation. A test split of about 80 items gives wide confidence intervals. Results would describe one 2016 licence consultation only.
- **Tweets:** up to 1,500 items, but stance coverage depends on how many tweets have a policy target (D5). Person/party-only tweets are excluded.
- **Not stance data:** CIVIS and Lok Sabha are retrieval/context sources and never stance examples. Sentiment140, the Hinglish sentiment sets and the weak predictions are quarantined.
- **Transformers:** none are planned at this scale on 8 GB RAM.

# Stance Classification — Model Experiment Plan

**Status:** planning document only. **No model in this plan has been
trained, downloaded, or run.** This plan becomes actionable once
`ml/stance_classification/dataset_prep.py` has produced real train/val/test
splits from a **finalized** human annotation export (see
[`ANNOTATION_WORKFLOW.md`](../dataset/ANNOTATION_WORKFLOW.md)) — not before.
Hardware feasibility for every experiment below is assessed in
[`HARDWARE_FEASIBILITY_REPORT.md`](HARDWARE_FEASIBILITY_REPORT.md).

## Shared setup (applies to all four experiments)

- **Data source:** `data/processed/stance_classification_splits/{train,val,test}.csv`,
  produced by `ml/stance_classification/dataset_prep.py` from the finalized
  single-annotator export. Labels: `Support` / `Oppose` / `Neutral` /
  `Unclear` only — exclusion-coded rows are never classification targets
  (rule D8).
- **No pseudo-labels, no AI-predicted labels, anywhere in training or
  evaluation data for any experiment below.** If a future phase wants to
  explore semi-supervised or pseudo-labeling techniques, that is an
  explicitly separate, explicitly scoped decision — not an extension of
  this plan.
- **Evaluation metrics, common to all four:** macro-F1 (primary — the four
  classes are imbalanced, per `SINGLE_ANNOTATOR_PROTOCOL.md` section 4.2's
  ~8–12% estimated Oppose base rate, and macro-F1 doesn't let the majority
  class hide poor performance on the rest), per-class precision/recall/F1,
  and the full 4x4 confusion matrix. Accuracy is reported but never used
  as the primary criterion, for the same reason.
- **Reproducibility:** every experiment fixes and records a random seed,
  the exact split manifest hash it was trained against
  (`split_manifest.json`'s `source_sha256`), and its own hyperparameters,
  mirroring the pattern `dataset_prep.py` already establishes.
- **No experiment here is assumed to be "the" final model.** This plan's
  purpose is comparison, not pre-committing to one architecture.

## Experiment 1 — TF-IDF + Logistic Regression

- **Research hypothesis:** a linear model over sparse lexical features
  (word/n-gram presence and frequency) captures enough signal to beat a
  majority-class baseline on this corpus's stance task, because the
  taxonomy's D1 ("direction over tone") rule means a lot of the signal is
  genuinely lexical (explicit agree/disagree/reject/support vocabulary),
  not deeply contextual.
- **Input features:** TF-IDF over `normalized_text` (word-level, 1–2 grams,
  English stopwords removed as a starting config — revisit if French rows
  are later included per `SINGLE_ANNOTATOR_PROTOCOL.md` section 10's
  French follow-up batch, since stopword lists are language-specific).
- **Training requirements:** `sklearn.feature_extraction.text.TfidfVectorizer`
  + `sklearn.linear_model.LogisticRegression` (`class_weight="balanced"`
  given the expected class imbalance). Fits in seconds on a dataset this
  size.
- **Evaluation metrics:** as in "Shared setup." Additionally: inspect
  learned per-class top-weighted terms as a sanity/interpretability check
  (does "Oppose" surface negation/rejection vocabulary, etc.) — this is
  diagnostic, not a metric to optimize against.
- **Memory requirements:** well under 200 MB; the sparse TF-IDF matrix at
  this corpus scale is tiny.
- **CPU feasibility:** trivial — full train+eval cycle in well under a
  minute.
- **Comparison criteria:** macro-F1 on the validation split against the
  other three experiments; also the cheapest experiment to iterate on, so
  it doubles as the fast feedback loop for annotation-quality sanity
  checks (e.g., "does the model at least separate Support from Oppose
  reasonably once N00+ examples of each exist").
- **Expected limitations:** no contextual understanding — will struggle
  exactly where the taxonomy's hard rules (D2 provision-scope, D3
  conditionals, D4 implementation-vs-substance, D7 sarcasm) require
  reading the whole comment's structure, not just its vocabulary. Expect
  this model's errors to cluster on `Unclear`/borderline items (the
  taxonomy's own hardest category for a human, let alone a bag-of-words
  model).

## Experiment 2 — TF-IDF + LinearSVC

- **Research hypothesis:** a max-margin linear classifier over the same
  lexical features as Experiment 1 may generalize better than logistic
  regression on a small, imbalanced dataset, where LogReg's probability
  calibration isn't the point — class separation is.
- **Input features:** identical TF-IDF features to Experiment 1, so the
  comparison isolates the effect of the classifier, not the features.
- **Training requirements:** `sklearn.svm.LinearSVC` (`class_weight="balanced"`).
  No probability estimates by default (would need `CalibratedClassifierCV`
  if probabilities are later wanted for downstream thresholding) — not
  needed for this comparison.
- **Evaluation metrics:** identical to Experiment 1 for direct comparability.
- **Memory requirements:** comparable to Experiment 1, well under 200 MB.
- **CPU feasibility:** trivial, same order as Experiment 1.
- **Comparison criteria:** macro-F1 vs. Experiment 1 at identical features
  — the cleanest possible "does the classifier choice matter more than the
  features" comparison in this plan.
- **Expected limitations:** same lexical-only ceiling as Experiment 1;
  LinearSVC's lack of native probability output is a real limitation if a
  later use case wants confidence-thresholded predictions (e.g., "only
  auto-surface predictions above X confidence for review") — flag this
  explicitly rather than silently working around it with an uncalibrated
  decision-function score standing in for a probability.

## Experiment 3 — Sentence-BERT embeddings + classifier

- **Research hypothesis:** dense sentence embeddings that capture semantic
  similarity (not just lexical overlap) will outperform the TF-IDF
  baselines specifically on the taxonomy's harder cases — D2 (provision-
  scope vs. whole-policy), D3 (conditionals), and D4 (implementation vs.
  substance) all hinge on sentence-level meaning that a bag-of-words model
  can't represent.
- **Input features:** sentence embeddings from a small, CPU-friendly
  pretrained SBERT model (`sentence-transformers/all-MiniLM-L6-v2` — 384-dim,
  ~90 MB, multilingual variants exist if the French follow-up batch
  proceeds) over `normalized_text`. The SBERT model itself is used
  **frozen** for embedding extraction, not fine-tuned, in this experiment
  — fine-tuning a transformer is Experiment 4.
  **Note:** using this model requires a one-time download from the
  Hugging Face Hub on first use; per Phase F's hardware-respecting
  practices, this download happens once, the model is reused from local
  cache afterward, and no download happens as part of merely planning
  this experiment.
- **Training requirements:** encode once (`model.encode(texts, batch_size=32)`),
  cache the resulting embedding matrix to disk (`ml/embeddings/`), then
  train a lightweight classifier on top — logistic regression or
  LinearSVC again, so Experiment 3 vs. 1/2 isolates the effect of the
  *features* (lexical vs. semantic), the same way Experiment 2 isolated
  the effect of the *classifier*.
- **Evaluation metrics:** identical to Experiments 1–2.
- **Memory requirements:** ~400–600 MB peak (model weights + embedding
  matrix for a few hundred short comments is small; most of the footprint
  is the model and the PyTorch/transformers runtime itself, not the data).
- **CPU feasibility:** yes — embedding a few hundred short comments on
  CPU is a matter of seconds to a couple of minutes, not hours.
- **Comparison criteria:** macro-F1 vs. Experiments 1–2, with particular
  attention to whether the *gap* (if any) concentrates on the D2/D3/D4
  hard cases as hypothesized, by cross-referencing confusion-matrix errors
  against which decision rule each `annotation_notes` entry cites (where
  provided) — a qualitative error-analysis step, not just a single number.
- **Expected limitations:** at a pilot-scale dataset (on the order of
  ~150–200 labeled training examples after the 70/15/15 split, per
  `SINGLE_ANNOTATOR_PROTOCOL.md`'s 250-item batch), a few hundred frozen
  embeddings may not give the downstream classifier enough examples per
  class to actually exploit the richer representation — this experiment
  may not clearly beat the TF-IDF baselines at this sample size even if
  the hypothesis is directionally correct; that outcome is itself useful
  information about how much data this task needs, not a failure of the
  experiment design.

## Experiment 4 — Transformer-based stance classification (conditional)

- **Research hypothesis:** fine-tuning a transformer directly on this
  task (rather than using a frozen embedding + linear head) could capture
  task-specific distinctions the frozen SBERT embedding doesn't surface —
  **but this is only worth testing once there is enough labeled data and
  hardware headroom to do it properly**, per
  `HARDWARE_FEASIBILITY_REPORT.md`.
- **Input features:** raw (or lightly normalized) `comment_text`, tokenized
  by the transformer's own tokenizer — no separate feature engineering.
- **Training requirements:** a small model (`distilbert-base-uncased` or
  similar, ~66M params) via `transformers.Trainer`, small batch size
  (8–16), short max sequence length (the corpus's own word-count
  distribution supports this — see `HARDWARE_FEASIBILITY_REPORT.md`),
  few epochs (overfitting risk is high at pilot-batch scale).
- **Evaluation metrics:** identical to Experiments 1–3, plus explicit
  **overfitting monitoring** (train vs. val loss/F1 divergence per epoch)
  given how easy it is to overfit a large model to a few hundred examples.
- **Memory requirements:** 2–4+ GB during training (model + optimizer
  states + gradients), the largest footprint of any experiment in this
  plan, and the one most likely to be genuinely tight on an 8 GB machine
  alongside normal desktop usage.
- **CPU feasibility:** technically possible, slow — see
  `HARDWARE_FEASIBILITY_REPORT.md` for why this is "yes, but not
  recommended yet" rather than a clean "yes."
- **Comparison criteria:** macro-F1 vs. Experiments 1–3; given the
  overfitting risk, a result that merely *matches* Experiment 3 at several
  times the training cost and memory footprint should be read as "not
  worth it at this data scale," not as a tie.
- **Expected limitations:** this is the experiment most likely to overfit,
  least likely to justify its cost at the current single-annotator batch
  size, and the clearest candidate to defer to a future phase with (a)
  more labeled data and (b) GPU access (the project's own stated "future
  college lab" option). **Recommendation: run Experiments 1–3 first; only
  attempt Experiment 4 if Experiment 3 shows a meaningful gap over the
  TF-IDF baselines that a transformer might widen further, and only on
  hardware better suited to it than this machine.**

## Why no experiment here is assumed to be "the best" in advance

Per the project's own instruction: **do not assume the most complex model
is the best model.** At a pilot-scale, single-annotator dataset, a linear
model over TF-IDF features is a perfectly serious contender, not a
strawman baseline — it is cheap to iterate on, easy to interpret, and may
well be *more* reliable than a frozen-embedding or fine-tuned model when
there isn't much data to estimate a more complex decision boundary from.
The comparison in this plan is designed to let the data answer that
question, not to pre-ordain a winner.

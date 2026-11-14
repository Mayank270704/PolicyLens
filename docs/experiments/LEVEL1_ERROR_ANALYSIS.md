# Level 1 — Error Analysis and Data Sufficiency Review

**Status:** analysis only. No model was trained or tuned, no hyperparameter
was changed, no annotation or split file was modified, and the
development-exposed test split was not loaded or scored. The four saved
Experiment 1–3 models were only run for inference on the 38-row validation
split; the recomputed validation metrics match each saved report exactly.

**Privacy:** this file is in a git-tracked directory. It cites comment IDs,
aggregate counts and short paraphrases only — no verbatim comment text or
annotator notes. Full examples remain in the gitignored
`models/stance/*/evaluation_report.json` files.

Every claim below is tagged **[Observed]** (measured from repository data),
**[Assumption]** (a stated planning premise), or **[Recommendation]**.

## 1. Evidence base

| Model | Validation macro-F1 | Validation accuracy | Val. Oppose recall | Val. Neutral recall | Val. Unclear recall | Support↔Oppose confusions |
|---|---|---|---|---|---|---|
| E1 TF-IDF + LogReg | 0.297 | 0.342 | 0.25 | 0.125 | 0.417 | 3 |
| E2 TF-IDF + LinearSVC | 0.259 | 0.368 | 0.00 | 0.125 | 0.417 | 3 |
| E3 negation-aware LogReg | 0.331 | 0.342 | 0.25 | 0.25 | 0.417 | 1 |
| E3 negation-aware LinearSVC | 0.287 | 0.316 | 0.25 | 0.125 | 0.333 | 3 |

[Observed] Validation has 38 comments: Support 14, Oppose 4, Neutral 8,
Unclear 12. Every row above was selected on this same set, so the best
figure (0.331) is optimistically biased.

[Observed] With 4 Oppose items, Oppose recall can only be 0, 0.25, 0.5,
0.75 or 1.0. The 95% Wilson interval for 1/4 is **0.05–0.70**; for
Neutral 2/8 it is 0.07–0.59; for Unclear 5/12 it is 0.19–0.68. These
intervals overlap for every model, so no per-class difference between
experiments is distinguishable from noise.

## 2. Validation error analysis

### 2.1 Errors are shared across experiments

[Observed] Of 38 validation comments, **22 are misclassified by all four
models**, 9 by one to three models, and 7 by none. Changing the classifier
(E1 vs E2) or the preprocessing (E3) moved only the 9 "split" comments; the
22-comment core is unaffected by anything tried so far.

[Observed] Prediction mixes differ: E2 predicts Support 19/38 times and
Oppose once; E1 predicts Oppose 6 times with 1 correct. The E3 drop in
Support↔Oppose confusions (3 → 1) for LogReg is a two-comment change.

### 2.2 Error categories

Each of the 31 comments misclassified by at least one model is assigned one
primary category by the analyst, from the comment text, its prompt
(`policy_section`) and the annotator's note. Assignments are judgments;
counts are small and should be read as patterns, not prevalence estimates.

| Category | n | Comment IDs | Evidence |
|---|---|---|---|
| **Lexical negation — stance negation not captured** | 2 | PL-003966, PL-008727 | PL-003966 says it is "not in favour" of a proposal; `favour` occurs in **0** training comments, so the negation has nothing to attach to — all four models miss it. PL-008727 (negated claim about open government) is wrong in E2 and **fixed by both E3 models** — the only clear negation-handling gain. |
| **Lexical negation — non-stance negation misleads** | 2 | PL-001673, PL-006082 | Negation inside a clarification ("…not protected…") or a description of other people (…"don't understand"…), not a position. PL-001673 (a Support proposal) is predicted Oppose by all four models; PL-006082 flips to Oppose only in E3-SVC. |
| **Sarcasm / dismissive rhetoric** | 1 | PL-008939 | Dismissive, misspelled one-liner; key word (`retoric`) occurs in 0 training comments. All four models predict Unclear. |
| **Implicit opposition** | 1 | PL-008749 | Opposition expressed through contrast and a misspelled "non-existent" (0 training occurrences), with a superficially positive word earlier. Predicted Support by three models. |
| **Implicit support (proposals without evaluative words)** | 7 | PL-005083, PL-006418, PL-001422, PL-004304, PL-005817, PL-005379, PL-009780 | Recommendations, requests to restore/fund something, or a bare topic name, labelled Support because they advocate for openness. Contain no explicit approval vocabulary; models predict Unclear/Neutral. |
| **Explicit stance words never seen in training** | 2 | PL-003873, PL-003951 | Explicit enthusiasm ("love", "exciting") — both words occur in 0 training comments. Hashtags/URLs dominate the remaining tokens. |
| **Contextual — questions / information requests** | 3 | PL-004144, PL-004473, PL-000328 | Neutral clarifying questions. The default tokenizer discards `?`, so question form is invisible; PL-004473 is predicted Support by all four models. |
| **Contextual — prompt-dependent answers** | 2 | PL-009559, PL-009461 | Answers to Q18 ("knowledge/experience willing to share") listing expertise or topics — Neutral **because of the prompt**, which the models never see (they use `normalized_text` only). |
| **Contextual — tone without stance (D1)** | 2 | PL-000423, PL-008591 | Positive or critical tone with no evaluative direction; models follow the tone. |
| **Annotation boundary — Unclear used for off-topic** | 5 | PL-006162, PL-006277, PL-005477, PL-006805, PL-006400 | Annotator note states the comment is not related to the open-government policy. Under the guidelines (§5, D8) these fit `OFF_TOPIC`, not Unclear. Models predict Support/Neutral from the comment's own advocacy. |
| **Annotation boundary — Unclear used for "no position"** | 2 | PL-008456, PL-000731 | Note says no position is expressed — the wording the definitions give for Neutral. |
| **Annotation boundary — Neutral vs Support for suggestions** | 1 | PL-008193 | Constructive suggestion labelled Neutral, while similar suggestions (e.g. PL-005083, PL-005096) are labelled Support. |
| **Genuinely unresolved intent** | 1 | PL-007687 | A call to repeal transparency legislation with no reason given; the annotator marks intent unclear. Models split Support/Oppose. |

[Observed] "Unclear" predictions are wrong for different reasons: on true
Neutral items they follow experience statements (PL-009559, PL-000423); on
true Support items they reflect missing advocacy vocabulary (PL-005083,
PL-003873); on true Oppose items they reflect unseen stance words
(PL-003966, PL-008939). They are not one failure mode.

[Observed] Annotator confidence does not predict model error: 15 of the 22
all-four-wrong comments are confidence 3 (High).

### 2.3 Why lexical features have little to work with

- [Observed] Explicit stance vocabulary is almost absent from training:
  `oppose`, `against`, `favour`, `repeal`, `disappointing`, `love`,
  `exciting` occur in **0** of 175 training comments; `support` occurs in 3,
  `agree` in 1.
- [Observed] Using an illustrative analyst lexicon of explicit positive and
  negative words, only 4 of 20 training Oppose comments contain any explicit
  negative word, and explicit negative words also appear in 7 Unclear and 5
  Support comments. [Assumption] The lexicon is illustrative, not validated.
- [Observed] Negation is spread across all classes (training comments
  containing a negation/contrast word: Support 15, Oppose 9, Neutral 10,
  Unclear 20); E3-LogReg weights `not` toward Unclear (+1.11) more than
  Oppose (+0.76).
- [Observed] Only 42% of validation tokens are in the E3-LogReg vocabulary
  (309 features; 63% for E3-SVC's 1,225).
- [Observed] The prompt (`policy_section`) is not a model input, although
  label mix depends strongly on it (train+val): Q14 "Please tell us why"
  (a follow-up to a satisfaction rating that is **not in the data**) is
  26% Oppose (11/42) versus 7.6% for all other prompts (13/171), and holds
  11 of 24 Oppose comments; Q8 "Did we miss anything?" is 51% Unclear
  (22/43).

## 3. Annotation-label findings (train + validation only, n = 213)

The test split's notes were deliberately not analysed.

- [Observed] **Unclear is mostly not "mixed".** Of 66 Unclear notes, the
  analyst groups them as: off-topic / not related to the policy **22**
  (33%); no position expressed (event shares, greetings, bare topics) **35**
  (53%); referenced context missing (reply to an unavailable earlier comment)
  **2**; genuinely unresolved intent or target **6** (9%); placeholder note
  **1**. No note explicitly describes balanced support and opposition (D5).
- [Observed] **The same rationale yields two labels.** "No position
  expressed"-type wording appears in 21 of 45 Neutral notes and 25 of 66
  Unclear notes.
- [Observed] **`OFF_TOPIC` was never used**: 0 exclusions in the 250-row
  batch, despite 22 train+val Unclear notes describing off-topic content.
- [Observed] **Support is sometimes inferred from topic naming**: 7 of 78
  Support notes say the comment "implies" support (e.g. a bare topic name).
- [Observed] One Unclear label (PL-001777) has the note "." although notes
  are required for every Unclear label; the validator does not catch this
  because it only checks for a blank note.
- [Observed] No note cites a decision-rule code (D1–D8); the guidelines
  encourage this for non-trivial cases.

Consequence: [Observed] a large share of the current Unclear class behaves
like "off-topic or no position", overlapping Neutral and the exclusion
codes. Some model "errors" on Unclear and Neutral are therefore
disagreements with a label boundary that is itself inconsistently applied —
not purely model failure.

## 4. Data sufficiency

### 4.1 Current class counts

[Observed]

| Split | Support | Oppose | Neutral | Unclear | Total |
|---|---|---|---|---|---|
| Train | 64 | 20 | 37 | 54 | 175 |
| Validation | 14 | 4 | 8 | 12 | 38 |
| Test (exposed; counts from manifest only) | 13 | 5 | 8 | 11 | 37 |

[Observed] Limitations caused by the small Oppose class: 20 training
examples cannot cover the vocabulary of opposition (§2.3); 4 validation
examples make Oppose recall a 5-valued, ±0.49 measurement; and macro-F1
gives Oppose 25% weight, so one validation comment can move macro-F1 by
several points.

### 4.2 Planning estimates

**These are planning estimates under stated assumptions, not statistical
guarantees or learning-curve results.**

Assumptions:
- [Assumption A1] Future batches use the same proportional stratified
  random sampling as `annotation_batch_001`, so Oppose arrives at the
  observed 11.6% per annotated comment. Sensitivity uses the
  historical-file rates 8.2% and 4.75% (unverified provenance).
- [Assumption A2] 70/15/15 split, as now.
- [Assumption A3] ≥100 training examples per class is a reasonable *minimum*
  for a lexical linear model to see varied stance vocabulary; 50 is a
  weaker interim target. This is a heuristic — no learning curve exists yet.
- [Assumption A4] For a per-class recall estimate of about ±0.15 (95%,
  worst case p = 0.5), a class needs ≈43 evaluation examples.
- [Assumption A5] Active annotation time ≈51.9 s per comment (median from
  86 GUI save events; covers only part of batch_001 and excludes breaks) —
  likely a lower bound.
- [Assumption A6] Applying `OFF_TOPIC` more strictly removes non-Oppose
  comments, so it does not change Oppose yield per annotated comment.

| Target (driven by Oppose) | At 11.6% | At 8.2% | At 4.75% |
|---|---|---|---|
| ≥50 Oppose in training | 621 total (+371; ~5 h) | 879 (+629) | 1,516 (+1,266) |
| ≥100 Oppose in training | 1,233 total (+983; ~14 h) | 1,744 (+1,494) | 3,011 (+2,761) |
| ≥43 Oppose in a 15% validation split | 2,475 total (+2,225) | 3,500 (+3,250) | 6,043 (+5,793) |
| Separate sealed test batch with ≥43 Oppose | 371 comments | 525 | 906 |

Other planning facts:
- [Observed] The eligible pool (protocol §4.1) has 7,941 comments, 7,691
  still unlabelled, so every target above except the 4.75% validation
  target is feasible from the existing pool.
- [Observed] Q14 responses are ~3.4× richer in Oppose than other prompts
  (26.2% vs 7.6%).
- [Recommendation] Q14-weighted sampling could cut the cost of the training
  targets substantially, but it changes class priors. Use it for training
  data only, record selection probabilities, and keep evaluation sets on
  proportional random sampling. The size of the Q14 sub-pool was not
  verified here.

## 5. Protocol review — recommendations (protocol not modified)

[Recommendation] Clarify, before any further annotation:

1. **Genuinely Unclear comments.**
   - Restrict Unclear to (a) D5 mixed or contradictory positions, (b)
     stance-bearing comments whose direction or target cannot be resolved
     (D3/D7), and (c) replies whose referenced content is unavailable.
   - State explicitly that "no position expressed" is **Neutral**, and that
     content unrelated to open government is **`OFF_TOPIC`**, not Unclear.
   - Add worked examples of each.
2. **Policy scope.** Define what counts as "the policy" for prompts like Q8
   ("Did we miss anything?") and Q18 (expertise). Is a suggestion about
   immigration or financial literacy off-topic, or an on-topic suggestion
   for the government agenda? The current notes treat it as off-topic but
   label it Unclear.
3. **Implicit support/opposition.** State whether a recommendation, a
   request to restore or fund something, or a bare topic name counts as
   Support, and when it should be Neutral instead. Currently similar
   suggestions receive both labels. Add a parallel rule for implicit
   opposition (dismissal, "same old", "non-existent").
4. **Sarcasm.** D7 covers ambiguous sarcasm. Add examples of *resolvable*
   dismissive or sarcastic comments (labelled by intended direction) versus
   unresolvable ones (Unclear and flagged).
5. **Negation that is not a stance signal.** Add a note that negation inside
   a clarification, a description of others, or a statement of personal
   circumstance does not by itself indicate Oppose, with examples.
6. **Q14 context.** Q14 answers explain a satisfaction rating (Q13) that
   annotators and models do not see. Either recover and display the rating,
   or document how to label Q14 without it.
7. **Note quality.** Require a non-placeholder note and a rule code (D1–D8)
   for Unclear and Oppose labels. A validator check for notes shorter than a
   few words would catch PL-001777.

[Recommendation] Any change to existing labels should go through the
adjudication log (guidelines §7), not by editing annotation files.

## 6. Technical recommendation

**Is the current dataset sufficient for a credible four-class classifier?**
No.
- [Observed] The four-class signal at this scale is close to chance:
  macro-F1 0.26–0.33 on a reused 38-item validation set, with wide,
  overlapping confidence intervals.
- [Observed] Key stance vocabulary is absent from training.
- [Observed] The Unclear/Neutral/`OFF_TOPIC` boundary is applied
  inconsistently.
- [Observed] No untouched test set remains.

**Minimum sensible next data-collection step** [Recommendation], in this
order:
1. Agree the §5 clarifications.
2. Complete the repeat-annotation pass when its gate opens (2026-11-22) and
   review Unclear/Neutral flips specifically.
3. Annotate **`annotation_batch_002` of ~400 comments** by proportional
   random sampling under the clarified protocol, and **seal it as the new
   Level 1 test set** (expected ~46 Oppose at 11.6%).

Creating the sealed test set before further model iteration prevents a
repeat of the current test exposure. Training-data growth (toward the
≥100-Oppose target, optionally Q14-weighted) comes after.

**What should remain unchanged** [Recommendation]:
- The four labels and rules D1–D8.
- The finalized batch_001 file and its backup (corrections only via
  adjudication).
- Leakage-safe group splitting and `validate_splits.py`.
- Train-only fitting, validation-only selection, and the single-use test
  guard.
- Negation-aware preprocessing for any future lexical model.
- Hash-verified, versioned, gitignored artifacts.
- No historical unverified labels and no pseudo-labels.

**Evidence required before declaring Level 1 complete** [Recommendation]:
1. Repeat-subset intra-annotator kappa ≥ 0.61 (protocol §9 default), with
   any systematic Unclear/Neutral disagreement resolved in the guidelines.
2. The §5 clarifications documented, and any relabelling logged through
   adjudication.
3. A sealed, randomly sampled test set never used in development, with
   enough examples per class for ±0.15 recall precision (≈43 Oppose).
4. A success threshold fixed **before** test evaluation. For example: the
   lower 95% bootstrap bound of test macro-F1 exceeds both the
   majority-class baseline and the best Experiment 1–3 lexical baseline.
   Per-class recall must be reported with confidence intervals, and every
   class must be predicted.
5. A learning curve on development data, showing whether additional labels
   are still improving performance.
6. Error analysis repeated on the new test set.

## Appendix — files read for this report

- `models/stance/tfidf_logreg_v1/`: evaluation report, config, metadata and
  model artifacts (inference only).
- `models/stance/tfidf_linearsvc_v1/` and `models/stance/negation_tfidf_v1/`:
  the same.
- `data/processed/stance_classification_splits/train.csv`, `val.csv` and
  `split_manifest.json`. `test.csv` was not read.
- `docs/dataset/STANCE_LABEL_DEFINITIONS.md`,
  `STANCE_ANNOTATION_GUIDELINES.md` and `SINGLE_ANNOTATOR_PROTOCOL.md`
  (§4, §5, §6, §9, §10).
- `docs/experiments/STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md`.
- `ml/stance_classification/tfidf_logreg.py`, `tfidf_linearsvc.py` and
  `negation_tfidf.py`.

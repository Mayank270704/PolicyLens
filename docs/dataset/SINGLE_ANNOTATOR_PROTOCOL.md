# Single-Annotator Stance Annotation Protocol

**Status:** Methodology for a new annotation experiment. No comments have been
labeled, no historical annotation data has been modified, and no model has
been trained as a result of this document or its accompanying files.

**Annotator:** Exactly one human annotator — the project owner. There is no
second annotator in this protocol. Any agreement statistic produced under
this protocol is **intra-annotator (test-retest) reliability**, never
inter-annotator agreement, and the resulting labels are **not** to be called
gold-standard prior to that validation step (see
[Section 9](#9-validation-status--what-this-is-not)).

**Normative references (read first):**
- [`STANCE_LABEL_DEFINITIONS.md`](STANCE_LABEL_DEFINITIONS.md) — the four
  final labels (Support / Oppose / Neutral / Unclear) and decision rules
  D1–D8.
- [`STANCE_ANNOTATION_GUIDELINES.md`](STANCE_ANNOTATION_GUIDELINES.md) — the
  workflow, exclusion criteria, and (Section 6) the Cohen's/Fleiss' kappa
  convention this protocol adapts to the single-annotator, repeated-measures
  case.
- [`STANCE_ANNOTATION_EXAMPLES.csv`](STANCE_ANNOTATION_EXAMPLES.csv) — worked
  examples for calibration before annotating.

**Deliverables produced alongside this document:**
- `data/annotations/new_experiment/annotation_batch_001.csv` — 250 blank
  annotation rows, ready for manual labeling.
- `data/annotations/new_experiment/repeat_annotation_plan.json` — the hidden
  repeat-subset design and the intra-annotator kappa methodology.

---

## 1. Corpus inspected

Primary corpus: `data/processed/canonical_corpus/unique_texts.csv`.

| Property | Value |
|---|---|
| Total unique texts (csv-parsed row count) | 10,043 (one row per `unique_id`) |
| Schema | `unique_id, corpus_id, multiplicity, source_dataset, source_record_id, question_slug, language, original_text` |
| `source_dataset` values | `consultation_compilation_2017_18` (4,819), `get_involved_questionnaire_2017_18` (4,780), `individual_comments_2016_18` (444) |
| `language` distribution | English 8,959; French 1,078; "S" 3; Arabic 2; Japanese 1 |
| `question_slug` distinct values | 9 (see [Section 5](#5-policy-context-and-policy-section-construction)) |
| Text length (words) | min 1, median 13, mean 23.8, p90 48, p95 74, max 1,136 |
| Text length (chars) | min 20 (eligibility floor), median 87, mean 149.7, max 7,229 |
| Exact duplicate `original_text` values | 0 (confirms "unique" in the filename) |

A note on the file's true row count: a naive `wc -l` on this CSV reports
10,804 lines, not 10,043 rows — several `original_text` values contain
literal embedded newlines inside quoted fields. All counts in this document
come from CSV-aware parsing (Python's `csv` module), not line counts.

**What this corpus actually is.** All three source datasets are public
engagement/survey feedback on the Government of Canada's Open Government
initiative (the "Get Involved" questionnaire and consultation-compilation
events feeding Canada's 3rd/4th Plan on Open Government, 2016–18). It is
**not** a single discrete policy document with numbered clauses in the style
of the synthetic P1–P4 examples in `STANCE_ANNOTATION_EXAMPLES.csv`. This
matters for rule D6 (policy-context requirement): there is no single
"policy text" to open and cross-reference section numbers against. See
[Section 5](#5-policy-context-and-policy-section-construction) for how this
protocol adapts D6 to the metadata that actually exists, and
[Section 10](#10-known-limitations) for what this means for annotators.

## 2. Historical datasets inspected (read-only — not modified)

Per the project restriction, the following were inspected for calibration
and leakage-avoidance only. **No file below was edited, relabeled, or
overwritten; no row was added or removed.**

| File | Rows | Labels used | Note |
|---|---|---|---|
| `data/annotations/previous_research/consolidated_stance_dataset_corrected.csv` | 600 | Support/Oppose/Neutral/Unclear | "600-row training" set |
| `data/annotations/previous_research/stance_human_gold_400_provisional.csv` | 400 | support/oppose/neutral/unclear (lowercase) | "400-row provisional evaluation" set |
| `data/annotations/previous_research/targeted_annotation_200/stance_targeted_master.csv` (+ `..._reviewer_blind.csv`, byte-identical copy) | 134 | blank (unlabeled) | A prior attempt to prepare a 200-row targeted batch under this same taxonomy; only 134 records were found eligible against a much broader exclusion set (see below) and the file was never labeled |

**Data-quality caveat (reported, not corrected — historical files are
read-only):** in both the 600-row and 400-row files, `annotator_A_label`
and `annotator_B_label` are **identical on every single row**
(`adjudication_status` is `not_required_agreement` / `not_required_full_
agreement` for 100% of rows, with zero disagreements). Genuine independent
double-annotation essentially never produces zero disagreement across
hundreds of rows for a nuanced 4-class task. This is flagged here precisely
because of the project's instruction not to call any dataset
gold-standard before validation — these two "historical" files should be
treated as **reference/calibration material of unverified provenance**, not
as validated ground truth, until/unless a separate audit confirms the
labels were produced by genuinely independent annotators. This protocol does
not attempt to fix or re-label them; it only avoids building the new sample
on top of them uncritically.

**Leakage check against the primary corpus.** Using the `unique_id` /
`unique_text_id` fields, all three historical files were confirmed to
reference real `unique_id`s in `unique_texts.csv`, and the three ID sets are
**mutually disjoint** (0 overlap between any pair): 600 ∩ 400 = 0,
600 ∩ 134 = 0, 400 ∩ 134 = 0. Their union is 1,134 of 10,043 unique texts
(11.3%).

**On the prior 134-row attempt's much stricter exclusion.** The
`sampling_manifest.json` for that attempt recorded a union-excluded set of
9,909 of 10,043 ids (98.6%), built from additional pools —
a "frozen_evaluation" set, an "active_model_training_pool," and a 9,515-row
"prior_in_domain_pseudo_training" pool of **AI-generated pseudo-labels**
used for prior model training — none of whose source files
(`data/full_corpus/run_v1/...`, `data/ai_labels/...`,
`data/stance_training_ai_working_labels/...`) exist anywhere in this
project. Those exclusions are therefore **not independently verifiable
here** and are not assumed valid for this protocol. This protocol instead
computes its own eligible pool directly from the three historical files that
do exist in this project (600 + 400 + 134 = 1,134 excluded ids), which is
both reproducible and auditable from files actually present in this
repository. The 134-row pool itself is additionally excluded from the new
sample's universe (not drawn from), since it was already deliberately set
aside by a prior process for a related purpose and left untouched here.

## 3. Length, language, and metadata analysis

- **Length:** word counts range from 1 to 1,136 (chars 20–7,229), heavily
  right-skewed (median 13 words, mean 23.8) — most comments are short
  survey responses, with a long tail of multi-paragraph submissions. This
  protocol stratifies by length tertile (see [Section 4](#4-sampling-strategy))
  so the batch isn't dominated by trivially short one-liners.
- **Language:** English is 89.2% of the corpus; French 10.7%; a combined
  0.06% is "S"/Arabic/Japanese (likely data-entry artifacts or
  misclassification for "S"). This protocol's batch is drawn from the
  **English-language eligible pool only** — see
  [Section 10](#10-known-limitations) for why, and how to extend.
- **Available metadata used for context:** `source_dataset`,
  `source_record_id`, `question_slug`, and (via
  `data/processed/canonical_corpus/corpus_entries.csv`) `stakeholder_group`
  and the original `source_field` label. For the
  `consultation_compilation_2017_18` subset specifically, `source_record_id`
  was joined back to the raw source file
  (`data/raw/original_sources/ConsultationData2017Engagement_...csv`,
  1-indexed spreadsheet row = `source_record_id`, verified by exact-text
  match before use) to recover row-level `Event`, `Context/Prompt`,
  `Subject`, `Theme`, and `Sub-theme` fields where present. No raw source
  files were modified; they were read-only joins.

## 4. Sampling strategy

### 4.1 Eligible pool

```
corpus (10,043)
  − historical_training_600       (600,  0 overlap with the two below)
  − historical_provisional_400    (400)
  − historical_targeted_134       (134, already set aside by a prior process)
  − non-English language rows     (968 of the remaining 8,909)
  = 7,941 eligible unique_id values
```

### 4.2 Sample size: 250

**Recommendation: n = 250 primary comments**, with a nested 38-item hidden
repeat subset (see [Section 7](#7-hidden-repeat-annotation-subset)), for a
total of ~288 single-annotator labeling events.

Why 250, not larger or smaller:

- **Workload is the binding constraint, by design.** This is a single
  annotator applying the full D1–D8 workflow per item — reading the full
  comment, checking for D6 provision references, and for the
  `consultation_compilation` stratum consulting the joined `Event` /
  `Context/Prompt` / `Theme` metadata, then writing a required justification
  note for every Unclear and D4-based Oppose label. That is materially
  slower than a quick sentiment tag. 250 items is large enough to be useful
  and small enough to be realistically completable (and, critically,
  *re-checkable* for the repeat subset) by one person across a small number
  of focused sessions, rather than degrading into fatigue-driven
  shortcuts late in the batch.
- **It clears the statistical floor for the reliability check this
  protocol exists to produce.** A repeat subset needs roughly ≥30 items for
  a stable Cohen's kappa point estimate; 15% of 250 (38 items, see
  [Section 7](#7-hidden-repeat-annotation-subset)) clears that floor with
  margin. A much smaller main batch (e.g. 100) would force an
  uncomfortably small repeat subset (~15 items) to hit the same percentage,
  or an uncomfortably large percentage to hit the same count.
- **It is large enough to populate all four labels, including the rare
  one.** The two (unverified-provenance) historical files suggest Oppose is
  the rare class (~8–12% base rate). At n=250 with proportional stratified
  sampling, that implies roughly 20–30 Oppose items — thin, but enough to
  sanity-check the label definitions against real examples rather than
  zero. This is a **pilot/calibration batch**, not a claim of a
  class-balanced or production-scale training set.
- **It matches this project's own precedent.** The abandoned 134-row
  attempt in [Section 2](#2-historical-datasets-inspected-read-only--not-modified)
  was itself targeting 200 and only fell short because of exclusions this
  protocol cannot verify. 250 sits just above that prior intended scale,
  using a pool (7,941 eligible) that is actually large enough to support
  it without re-touching anything already set aside.

250 is a recommendation sized to the stated constraints (one annotator, no
automated labeling, a required repeat-reliability check), not a
statistically "optimal" number — there is no fixed formula for single-rater
qualitative annotation sample size. If annotator capacity turns out to be
higher or lower than expected, `annotation_batch_002` can draw an
independently-seeded extension from the same eligible-pool definition in
[Section 4.1](#41-eligible-pool) (excluding `annotation_batch_001`'s 250 ids
in addition to the 1,134 historical ones) without redesigning the method.

### 4.3 Stratified sampling design

Stratified (not simple random) by `source_dataset` × length tertile (9
cells), proportional to each cell's share of the 7,941-item eligible pool,
with a floor of `min(3, cell size)` per cell so the smallest source
(`individual_comments_2016_18`, 405 eligible items) is never silently
dropped to zero — then fractional remainders are assigned to the cells with
the largest fractional shortfall until the total is exactly 250.

Length tertiles were computed **on the eligible pool itself** (word count):
short = 1–9 words, medium = 10–21 words, long = 22+ words.

| Stratum (dataset × length) | Eligible pool | Sampled |
|---|---|---|
| consultation_compilation_2017_18 × short | 1,322 | 41 |
| consultation_compilation_2017_18 × medium | 1,394 | 44 |
| consultation_compilation_2017_18 × long | 1,213 | 38 |
| get_involved_questionnaire_2017_18 × short | 1,243 | 39 |
| get_involved_questionnaire_2017_18 × medium | 1,097 | 34 |
| get_involved_questionnaire_2017_18 × long | 1,267 | 40 |
| individual_comments_2016_18 × short | 156 | 5 |
| individual_comments_2016_18 × medium | 196 | 6 |
| individual_comments_2016_18 × long | 53 | 3 |
| **Total** | **7,941** | **250** |

Resulting sample composition: `consultation_compilation_2017_18` 123,
`get_involved_questionnaire_2017_18` 113, `individual_comments_2016_18` 14;
length buckets short 85 / medium 84 / long 81; word count min 2, median 14,
mean 23.7, max 239.

### 4.4 Reproducibility

- Within-stratum selection: Python's `random.Random(20261108)` (seed =
  protocol creation date, `YYYYMMDD`), sampling without replacement, one
  shuffle-and-slice per stratum cell.
- Final row order: the per-stratum selections are concatenated and
  re-shuffled once with the same RNG stream before being written out (so
  stratum membership isn't visible from file order), then the output CSV is
  sorted by `comment_id` for stable, diffable storage.
- Given the same eligible-pool definition (Section 4.1) and the same seed,
  this selection is exactly reproducible from `unique_texts.csv` alone.

## 5. Policy context and policy section construction

The corpus has no single numbered policy document to cite, so `policy_
context` and `policy_section` are built from the richest metadata actually
available per `source_dataset`, rather than left as a placeholder:

- **`policy_context`** — a fixed, human-readable description of which Open
  Government engagement instrument the comment came from (one of the three
  `source_dataset` values), extended per-row where possible:
  - `consultation_compilation_2017_18`: appends the engagement `Event` name
    and `Context/Prompt` text, recovered by joining `source_record_id` back
    to the raw source CSV (verified against `original_text` before use;
    succeeded for 115 of the 123 sampled rows from this source — the
    remainder fall back to the dataset-level description only).
  - `individual_comments_2016_18`: appends the respondent's self-identified
    `stakeholder_group` (e.g., "Academia") from `corpus_entries.csv`.
  - `get_involved_questionnaire_2017_18`: dataset-level description only —
    this source is a fixed questionnaire with no per-response theme coding.
- **`policy_section`** — the specific prompt/question the comment is
  actually responding to, derived from `question_slug` (9 distinct values,
  hand-mapped to their real English question text from the raw
  questionnaire header, e.g. `q8` → *"Did we miss anything?"*, `q14` →
  *"Please tell us why"*), further extended with the joined `Theme` /
  `Sub-theme` for `consultation_compilation_2017_18` rows.

**Adapting rule D6.** Because there is no clause/section-numbered policy
document in this corpus, D6's instruction to "consult the relevant policy
document/section" is satisfied here by reading the `policy_context` +
`policy_section` fields provided on each row (the originating question and,
where available, event/theme) rather than a separate external document.
Annotators should still apply D6's spirit: if a comment references something
specific (a numbered plan, a named program) that the provided context
doesn't explain, that is grounds for an "Unclear" / needs-review flag rather
than guessing.

## 6. Annotation file: `annotation_batch_001.csv`

250 rows, stable IDs, blank label fields. Columns, in order:

| Column | Populated? | Notes |
|---|---|---|
| `comment_id` | Yes | Stable ID, `PL-<source_unique_id zero-padded to 6 digits>`, e.g. `PL-006861`. Derived from the corpus's own `unique_id`, which is stable across every file in this project (verified identical by SHA-256 across the migration audit) — `comment_id` is a deterministic, reversible re-encoding of it, not a new/fragile identifier. |
| `comment_text` | Yes | Verbatim `original_text`, unmodified. |
| `policy_context` | Yes | See [Section 5](#5-policy-context-and-policy-section-construction). |
| `policy_section` | Yes | See [Section 5](#5-policy-context-and-policy-section-construction). |
| `annotator_label` | **Blank** | One of exactly `Support` / `Oppose` / `Neutral` / `Unclear`. Left blank only when `exclusion_code` is set (rule D8). |
| `exclusion_code` | **Blank** | One of `SPAM` / `OFF_TOPIC` / `TOO_SHORT_NONSUBSTANTIVE` / `UNINTELLIGIBLE`, or blank if not excluded. Mutually exclusive with `annotator_label` being set — see [Section 6.1](#61-exclusion-codes-are-kept-separate-from-stance-labels). |
| `annotation_confidence` | **Blank** | `1` = Low, `2` = Medium, `3` = High. See [Section 6.2](#62-confidence-scale). |
| `annotation_notes` | **Blank** | Free text. Required for every Unclear label and every Oppose label reached via D4 (per `STANCE_ANNOTATION_GUIDELINES.md` §3 step 9); encouraged otherwise. |
| `source_unique_id` | Yes | The underlying `unique_texts.csv` `unique_id`, for traceability back to the corpus. Not required by the task spec; retained for auditability. |
| `source_dataset`, `language`, `word_count` | Yes | Provenance/metadata retained from the corpus, for post-hoc stratum analysis. Not annotation fields. |

No automated system populated, predicted, or suggested any value in
`annotator_label`, `exclusion_code`, `annotation_confidence`, or
`annotation_notes` — all four are blank in the delivered file and are
filled in exclusively by the human annotator.

### 6.1 Exclusion codes are kept separate from stance labels

Per rule D8 and `STANCE_ANNOTATION_GUIDELINES.md` §5: `exclusion_code` and
`annotator_label` are two different fields with mutually exclusive
semantics, not two values of one field. A row either gets a stance label
(and `exclusion_code` stays blank) or gets an exclusion code (and
`annotator_label` stays blank) — never both, and `Neutral` is never used as
a stand-in for exclusion (an off-topic/spam comment is `OFF_TOPIC`/`SPAM`,
not `Neutral`).

### 6.2 Confidence scale

A 3-point ordinal, chosen over a finer 5+ point scale because the taxonomy's
real decision boundaries (per `STANCE_LABEL_DEFINITIONS.md` D1–D8) are
qualitative rule applications, not fine-grained degrees of sentiment — a
coarse scale is faster for one annotator to apply consistently across 250
items and is sufficient to flag where adjudication-style review would help
later:

| Value | Meaning |
|---|---|
| `1` | Low — a rule had to be stretched, or the item is a genuine borderline case between two labels (e.g., Neutral vs. Unclear, or a D2/D4 net-direction call); treat as a candidate for the adjudication-style review in `STANCE_ANNOTATION_GUIDELINES.md` §7, even though there's no second annotator to adjudicate against here. |
| `2` | Medium — the label is reasonably clear after applying the decision rules, but required real reasoning (not a one-glance call). |
| `3` | High — unambiguous; a reader applying D1–D8 would not plausibly land anywhere else. |

## 7. Hidden repeat-annotation subset

Full design and the kappa methodology are in
`data/annotations/new_experiment/repeat_annotation_plan.json`. Summary:

- **38 of the 250** `comment_id`s (15.2%) are designated, in advance, as a
  hidden repeat subset — drawn uniformly at random (`random.Random(42)`,
  without replacement, from the finalized 250-item sample) **after** the
  stratified selection was locked in, so the repeat draw cannot bias which
  strata get re-checked.
- **First pass:** the annotator labels all 250 items in the normal
  workflow, not told which ids are repeats.
- **Minimum 14-calendar-day gap**, then **second pass:** the 38 repeat
  `comment_id`s are re-presented with blank label fields (no trace of the
  first-pass label), ideally interleaved into the start of a later batch
  rather than shipped as an obviously-labeled "consistency check" file, so
  the annotator isn't cued to try harder on exactly those items.
- Second-pass labels are recorded in a **separate** file
  (e.g. `repeat_pass_labels.csv`); `annotation_batch_001.csv` itself is
  never edited after its first pass.

### 7.1 Cohen's kappa for intra-annotator consistency

This reuses the exact kappa convention `STANCE_ANNOTATION_GUIDELINES.md` §6
already defines for two annotators, with "annotator B" replaced by "the same
annotator, second pass, ≥14 days later":

```
kappa = (p_o − p_e) / (1 − p_e)
```

- `p_o` = observed proportion of the 38 repeat items where pass-1 label ==
  pass-2 label.
- `p_e` = expected chance-agreement proportion, from the marginal label
  frequencies of pass 1 and pass 2 over those items.
- Computed **only** over items that received one of the four stance labels
  in **both** passes. Items excluded in either pass are removed from the
  kappa calculation and their exclude/don't-exclude agreement is reported
  as a **separate** raw agreement rate, since exclusion (D8) is a prior gate
  and not itself a stance category.
- Reference implementation:
  `sklearn.metrics.cohen_kappa_score(pass1_labels, pass2_labels,
  labels=['Support','Oppose','Neutral','Unclear'])` (`sklearn` is already
  present in this environment — nothing new to install), or the manual
  formula above for full auditability.
- Interpretation bands (Landis & Koch): <0 none, 0.00–0.20 slight,
  0.21–0.40 fair, 0.41–0.60 moderate, 0.61–0.80 substantial, 0.81–1.00
  almost perfect.

**This kappa is intra-annotator (test–retest) reliability only.** It must
never be reported or described as inter-annotator agreement — there is one
annotator in this protocol.

## 8. Strict restrictions honored by this protocol and its generated files

- No labels were generated, predicted, or assigned by any automated system.
  `annotator_label`, `exclusion_code`, `annotation_confidence`, and
  `annotation_notes` are blank in `annotation_batch_001.csv`.
- No AI predictions were used as, or substituted for, human annotations
  anywhere in this protocol.
- The historical files (`consolidated_stance_dataset*.csv`,
  `stance_human_gold_400_provisional.csv`,
  `stance_targeted_master.csv`/`_reviewer_blind.csv`) were read for
  inspection only; none were modified, relabeled, or overwritten.
- No model was trained.
- No dependencies were installed; analysis used only the Python standard
  library plus `pandas`/`numpy`/`scikit-learn`, which were already present
  in this environment (verified before use, not installed for this task).
- No git operations were run as part of producing this protocol or its
  files.
- This document does not claim inter-annotator agreement at any point — the
  only agreement statistic it defines (Section 7) is explicitly
  intra-annotator.
- Neither this document nor the generated files refer to
  `annotation_batch_001.csv` or its eventual labels as "gold-standard."
  See [Section 9](#9-validation-status--what-this-is-not).

## 9. Validation status — what this is not

`annotation_batch_001.csv`, once labeled, is a **provisional, single-
annotator pilot batch**. It becomes eligible to be treated as a validated
reference set only after:

1. The repeat-subset kappa (Section 7) is computed and falls in an
   acceptable band (project should set its own threshold — "substantial"
   per Landis & Koch, κ ≥ 0.61, is a reasonable default bar to propose, not
   assumed here), **and**
2. Any systematic disagreement pattern surfaced by the repeat subset (e.g.
   repeated D4 implementation-vs-substance flips between passes) has been
   reviewed and, if needed, the guidelines sharpened — mirroring
   `STANCE_ANNOTATION_GUIDELINES.md` §6's treatment of systematic
   disagreement as a guideline signal, not a one-off error.

Until both are done, this batch should be referred to as **provisional** or
**pilot**, exactly as the existing `stance_human_gold_400_provisional.csv`
naming already signals for its own (differently-sourced) contents.

## 10. Known limitations

- **Non-English comments (968 of the 8,909 otherwise-eligible pool, ~10.9%)
  are set aside, not sampled, in this batch.** The protocol defaults to an
  English-only batch because this document has no information confirming
  the single annotator's working proficiency in French (or the 3 "S"/
  Arabic/Japanese rows, which are likely data artifacts). A French-language
  follow-up batch can be drawn from the same eligible-pool definition
  (Section 4.1, minus the English rows already used) once that's confirmed
  — the sampling code and stratification approach extend directly.
- **D6's "policy document" requirement is adapted, not literally met** — see
  Section 5. There is no numbered-clause policy text in this corpus; the
  provided `policy_context`/`policy_section` are the richest available
  substitute from real metadata, not a fabricated policy document.
- **Rare-class counts will be thin.** At an estimated ~8–12% Oppose base
  rate (from the lower-confidence historical files), ~250 items yields
  roughly 20–30 Oppose examples — enough to pilot the guidelines against,
  not enough to assume reliable prevalence estimates.
- **The 134-row prior attempt's broader leakage logic could not be
  verified** (its source files don't exist in this project) and was
  therefore not inherited beyond excluding its own 134 ids; see Section 2.

# Stance Classification Methodology

**Status:** Proposed methodology. Under design. Not implemented, not trained,
not evaluated. All model and metric references below are provisional and
illustrative, pending dataset audit and literature review
(see [`PROJECT_STATUS.md`](../../PROJECT_STATUS.md)).

**Revision (2026-11-08):** The four-class taxonomy has been **finalized** as
**Support, Oppose, Neutral, Unclear**. The original draft of this document
proposed a separate **Mixed** category; Mixed has been merged into
**Unclear** and is no longer a distinct label anywhere in this document. The
finalized, authoritative label definitions, decision rules, annotator
workflow, exclusion criteria, and worked examples now live in:

- [`docs/dataset/STANCE_LABEL_DEFINITIONS.md`](../../docs/dataset/STANCE_LABEL_DEFINITIONS.md)
- [`docs/dataset/STANCE_ANNOTATION_GUIDELINES.md`](../../docs/dataset/STANCE_ANNOTATION_GUIDELINES.md)
- [`docs/dataset/STANCE_ANNOTATION_EXAMPLES.csv`](../../docs/dataset/STANCE_ANNOTATION_EXAMPLES.csv)

This document remains the research-methodology record (experimental
configurations, model candidates, training/evaluation strategy) and has been
updated below for terminology and rule consistency with the finalized
taxonomy. Where this revision changed a rule's outcome rather than just its
label name, that is called out inline with "**Revision (2026-11-08):**".

---

## 1. Problem definition and objectives

Given a government policy document `P` and a public comment `c` submitted in
response to `P`, the task is to assign `c` a stance label `y ∈ {Support,
Oppose, Neutral, Unclear}` that reflects the commenter's position toward the
policy (or a specific provision of it), as expressed in the text of `c`,
interpreted in light of `P`.

This is a **document-grounded stance classification** task, distinct from
general-purpose sentiment analysis, because the correct label for a comment
is only well-defined relative to what the policy actually proposes.

Objectives of this methodology:

1. Define stance categories precisely enough that independent human
   annotators can apply them consistently.
2. Specify how policy context is incorporated into the classification
   decision, not only the comment text.
3. Establish an experimental design that lets us measure, empirically,
   whether and how much policy context improves classification quality over
   comment-only sentiment analysis.
4. Keep the methodology model-agnostic at this stage: it constrains what is
   measured and how, not which specific model will ultimately be used.

## 2. Why comment-only sentiment analysis is insufficient

Generic sentiment analysis predicts whether text is positive, negative, or
neutral in affect. Stance toward a policy is a different construct for
several reasons:

- **Sentiment polarity and policy stance can diverge.** A comment written in
  a calm, neutral tone ("I think this provision should be removed") carries
  negative sentiment toward the tone but may encode clear **Oppose** stance.
  Conversely, an angry or sarcastic comment ("Finally, someone is doing
  something about this!") may carry negative-sounding affect while
  expressing **Support**.
- **Stance is relational, not intrinsic to the text.** "This will increase
  costs for small businesses" is Oppose if the policy's stated goal is to
  support small businesses, but could be Support if the policy's goal is
  cost internalization for environmental reasons and the commenter is noting
  this approvingly. The same sentence requires opposite labels depending on
  what the policy proposes and how the commenter frames it relative to that
  proposal.
- **Comments reference policy content without restating it.** Commenters
  frequently refer to specific clauses, sections, or numeric thresholds
  ("Section 4(b)'s cap is too low") without re-describing what those
  sections say. A model with no access to the policy text cannot resolve
  what "too low" means, or even what is being evaluated.
- **Topic relevance cannot be assessed without the policy.** Off-topic,
  procedural, or non-substantive comments (e.g., "When is the comment period
  closing?") are not meaningfully Support/Oppose/Neutral/Unclear in a
  sentiment sense, but need a defined treatment that depends on what counts
  as "on-topic" for a given policy. **Revision (2026-11-08):** such
  comments are handled through a documented pre-labeling exclusion step
  (see Section 6), not forced into any of the four stance labels.

For these reasons, stance classification in PolicyLens is treated as a
**policy-aware** task: policy content is a required input to the modeling
problem, not an optional enrichment.

## 3. Policy context and public comment as model inputs

The classification task is modeled as a function of a (policy context,
comment) pair, not the comment alone:

```
stance = f(policy_context, comment)
```

Two candidate forms of `policy_context` are considered, corresponding to the
experimental configurations in Section 8:

- **No policy context** — the comment alone (baseline, for comparison only).
- **Full policy document** — the complete text of `P`, or a fixed summary of
  it, used as shared context for every comment submitted against that
  policy.
- **Retrieved policy context** — a small set of passages or sections from
  `P` that are most relevant to the specific comment `c`, selected via a
  retrieval step (Section 7) rather than supplied in full.

The comment itself (`c`) is used verbatim as submitted, without paraphrasing
or normalization beyond standard text cleaning (defined separately in
preprocessing documentation, not in this file). Metadata that may
accompany a comment (e.g., submission timestamp, section reference tags, if
present in the source data) is treated as auxiliary and is out of scope for
the initial methodology; its potential use is noted as an open question in
Section 14.

## 4. Four stance categories

**Revision (2026-11-08):** this is the finalized taxonomy. The original
draft's fourth category was **Mixed**; it has been replaced by **Unclear**,
whose definition is broader (it also covers insufficient-information and
indeterminate cases, not only genuinely mixed ones). Authoritative
definitions live in
[`docs/dataset/STANCE_LABEL_DEFINITIONS.md`](../../docs/dataset/STANCE_LABEL_DEFINITIONS.md);
the table below is kept in sync with it.

| Label | Definition |
|---|---|
| **Support** | The comment expresses agreement with, approval of, or a request to retain/strengthen the policy or a specific provision of it, with no substantial expressed disagreement. |
| **Oppose** | The comment expresses disagreement with, rejection of, or a request to remove/weaken/reverse the policy or a specific provision of it, with no substantial expressed agreement. |
| **Neutral** | The comment does not express an identifiable stance toward the policy — e.g., it is purely informational, procedural, or a clarifying question — and clearly has no direction to resolve. |
| **Unclear** | Mixed opinions containing both support and opposition; conflicting positions; insufficient information to determine stance; or stance that cannot be confidently established even with full policy context. |

These categories are mutually exclusive and intended to be exhaustive: every
comment that is **eligible for stance labeling** receives exactly one of the
four labels. **Revision (2026-11-08):** off-topic, spam, too-short/
non-substantive, and unintelligible comments are **no longer captured under
Neutral**. They are handled by a documented pre-labeling exclusion step
(Section 6) with explicit reason codes, so they are retained in the dataset
but are not forced into any of the four stance labels — including Neutral,
which now strictly means "on-topic, but no evaluative direction," not
"off-topic." See
[`docs/dataset/STANCE_ANNOTATION_GUIDELINES.md`](../../docs/dataset/STANCE_ANNOTATION_GUIDELINES.md#exclusion-criteria)
for the exclusion reason codes.

## 5. Detailed classification rules and examples

### 5.1 General rule

Annotators and models should determine stance **relative to the policy's
stated proposal**, not relative to the status quo in the abstract, and not
relative to the annotator's own opinion of the policy.

### 5.2 Rule set

1. **R1 — Direction over tone.** Classify based on the direction of the
   argument (for/against the proposal), not the emotional tone of the
   language.
   - *Example:* "This is an outrageous overreach and must be stopped." →
     **Oppose** (strong tone, clear direction).
2. **R2 — Provision-level aggregation.** If a comment addresses multiple
   provisions of the same policy, determine stance per provision first, then
   aggregate: unanimous direction → **Support**/**Oppose**; split direction
   with no resolvable net position → **Unclear** *(Revision 2026-11-08: was
   Mixed)*.
   - *Example:* "I support the emissions cap but strongly oppose the
     exemption for existing facilities." → **Unclear**.
3. **R3 — Conditional support/opposition.** A comment that supports a
   policy *only if* a condition is met, or opposes it *unless* a condition is
   met, is classified by its net implied direction toward the policy **as
   written** (not as the commenter wishes it were written), unless the
   condition itself constitutes a substantive objection to a core provision,
   in which case see R4.
   - *Example:* "I'd support this if the deadline were extended, but as
     written, six months isn't enough time." → **Oppose** (the policy as
     written is rejected; the condition is a core objection, not a minor
     caveat).
   - *Example:* "This is a good policy overall, though I'd prefer a slightly
     longer grace period." → **Support** (the caveat is minor relative to
     overall endorsement).
4. **R4 — Substantive vs. minor caveats.** A caveat is "substantive" if
   removing it would require annotators to re-read the comment's core claim
   as reversed; it is "minor" if the comment's core claim stands independent
   of the caveat. Substantive caveats that make the comment genuinely
   irresolvable to one net direction push the label toward **Unclear**
   *(Revision 2026-11-08: was Mixed)*; minor caveats do not change the
   label. A caveat about **implementation/execution** rather than substance
   does not push toward Unclear either — see the implementation-criticism
   test added to R3 below.
   - **Revision (2026-11-08) — implementation vs. substance test.** Do not
     automatically classify criticism of *how* a policy will be implemented,
     enforced, or rolled out as a substantive caveat. Ask: *if the
     implementation concern were fully resolved, would the commenter's
     position flip?* If no, the concern is about execution, not substance,
     and the underlying Support/Oppose direction stands.
     - *Example:* "The fare hike makes sense for funding, I just hope they
       actually deliver the night service." → **Support** (concern is about
       follow-through, not the fare increase itself).
5. **R5 — No identifiable stance → Neutral; insufficient information →
   Unclear.** *(Revision 2026-11-08: narrowed.)* Purely factual statements,
   questions, or procedural remarks with no attempt at an evaluative
   position are **Neutral**. Comments that *engage* with the policy but
   provide too little content to resolve a direction (e.g., "This policy is
   complicated.") are **Unclear**, not Neutral — Neutral requires the
   comment to clearly have no direction to resolve, not merely to be brief.
   - *Example:* "What is the effective date of this rule?" → **Neutral**.
   - *Example:* "This policy affects farmers." → **Neutral** (factual, no
     evaluative direction).
   - *Example:* "I have thoughts on this but it depends on a lot of factors
     they haven't addressed." → **Unclear** (on-topic, but insufficient
     information to determine direction).
6. **R6 — Off-topic, spam, and non-substantive content → excluded, not
   labeled.** *(Revision 2026-11-08: was "Off-topic → Neutral.")* Comments
   unrelated to the policy's content, spam, comments too short or
   non-substantive to evaluate, and unintelligible text are **excluded from
   stance labeling entirely** using documented reason codes (`SPAM`,
   `OFF_TOPIC`, `TOO_SHORT_NONSUBSTANTIVE`, `UNINTELLIGIBLE`) — they do not
   receive Neutral or any other stance label. See
   [`docs/dataset/STANCE_ANNOTATION_GUIDELINES.md`](../../docs/dataset/STANCE_ANNOTATION_GUIDELINES.md#exclusion-criteria).
   Excluded comments remain in the dataset with their exclusion code
   recorded, so none are silently dropped.
7. **R7 — Sarcasm and rhetorical questions.** Resolve by the discernible
   intended direction, not literal text. If direction cannot be reliably
   discerned even with policy context — for example, sarcasm whose target
   is ambiguous between the policy itself and an unrelated claim about it —
   default to **Unclear** *(Revision 2026-11-08: was Neutral)* rather than
   guessing, and flag for adjudication (Section 10).
8. **R8 — Multiple distinct issues, one policy.** When a policy bundles
   unrelated issues (e.g., an omnibus policy) and a comment supports one
   bundled issue while opposing another, apply R2/R4 treating each bundled
   issue as a "provision."

### 5.3 Worked examples summary

| Comment (abridged) | Policy context needed | Label | Rule applied |
|---|---|---|---|
| "Finally, this protects workers like me." | Policy intent (worker protection) | Support | R1 |
| "This will bankrupt small shops; scrap it." | What the policy does to small business | Oppose | R1 |
| "I support the goal but the enforcement mechanism is unworkable." | Which part is "the goal" vs. "enforcement" | Unclear *(was Mixed)* | R2/R4 |
| "Could you clarify who this applies to?" | None beyond topic match | Neutral | R5 |
| "Great, more paperwork. Just what we needed." (sarcastic) | Policy's actual effect vs. commenter's framing | Oppose | R7 |

More worked examples, including borderline cases for every label, are in
[`docs/dataset/STANCE_ANNOTATION_EXAMPLES.csv`](../../docs/dataset/STANCE_ANNOTATION_EXAMPLES.csv).

## 6. Handling ambiguous, conditional, multi-issue, and excluded comments

- **Ambiguous comments** (insufficient information to determine direction,
  or genuinely indeterminate even with full policy context) are labeled
  **Unclear** *(Revision 2026-11-08: was Neutral with an `ambiguous=true`
  flag)*. Unclear is now the primary label for this case, not a sub-flag —
  it does not alter the four-category schema since Unclear is one of the
  four categories.
- **Excluded comments** (spam, off-topic, too-short/non-substantive,
  unintelligible) are identified via a **pre-labeling eligibility check**
  before any of R1–R8 are applied, and receive a documented exclusion
  reason code instead of a stance label. See R6 and
  [`docs/dataset/STANCE_ANNOTATION_GUIDELINES.md`](../../docs/dataset/STANCE_ANNOTATION_GUIDELINES.md#exclusion-criteria)
  for the full exclusion workflow and reason codes.
- **Conditional comments** follow R3/R4 above. Annotation guidelines will
  include a decision checklist (does the comment reject the policy as
  written? does the condition reverse the core claim?) to reduce
  inter-annotator disagreement on this category specifically, since pilot
  experience in related stance-detection literature suggests conditionals
  are a leading source of disagreement.
- **Multi-issue comments** follow R2/R8: decompose by provision/issue,
  aggregate by direction. Annotators record per-issue sub-judgments in the
  annotation tool (for analysis and potential future finer-grained labeling)
  even though only the aggregated four-way label is used for the primary
  classification task.
- All three categories above are expected to have **lower inter-annotator
  agreement** than clear-cut Support/Oppose cases. Agreement will be
  reported separately for these subsets (Section 10) rather than only in
  aggregate, so that difficulty is visible rather than averaged away.

## 7. Policy document section retrieval before classification

For the **policy-aware with retrieved context** configuration (Section 8),
classification is preceded by a retrieval step that selects a small number
of policy passages most relevant to a given comment, instead of supplying
the entire policy document as context for every comment.

Rationale:

- Policy documents can be long; supplying the full text for every comment is
  computationally expensive at the scale PolicyLens targets (up to hundreds
  of thousands of comments per policy) and may exceed practical context
  limits of candidate models.
- Most individual comments are relevant to only a small portion of the
  policy (a specific section or clause), so targeted retrieval is expected
  to provide a better signal-to-noise ratio than the full document.

Proposed retrieval pipeline (provisional, pending dataset audit):

1. **Segment** the policy document into sections/clauses using its existing
   structure (headings, numbered sections) where available, falling back to
   fixed-size overlapping chunks where structure is absent or unreliable.
2. **Embed** each segment and each comment using a shared sentence/document
   embedding model (specific model choice deferred — see Section 9).
3. **Score** segments against the comment by embedding similarity (e.g.,
   cosine similarity), optionally combined with lexical overlap scoring
   (e.g., BM25) as a hybrid retrieval signal, to mitigate failure cases where
   embeddings miss exact terminology matches (specific legal/technical terms,
   section numbers).
4. **Select top-k** segments (k to be determined empirically; not fixed in
   this methodology) as the retrieved context passed to the classifier.

Retrieval quality is itself an evaluation target (Section 12), not an
assumed-correct preprocessing step: retrieval errors (irrelevant or missing
sections) are expected to propagate into classification errors, and this
methodology treats that propagation as a measurable phenomenon rather than
discounting it.

## 8. Three experimental configurations

To isolate the contribution of policy context, three configurations are
defined and will be compared under identical data splits (Section 11) and
identical evaluation metrics (Section 12):

| Configuration | Input to classifier | Purpose |
|---|---|---|
| **A — Comment-only baseline** | Comment text only | Establishes the sentiment-analysis-equivalent lower bound; quantifies how much stance signal is recoverable from the comment alone. |
| **B — Policy-aware classification** | Comment text + full policy document (or a fixed policy summary) | Measures the effect of giving the model complete, un-retrieved policy context. |
| **C — Policy-aware with retrieved context** | Comment text + top-k retrieved policy passages (Section 7) | Measures whether targeted retrieval matches or exceeds configuration B at lower computational cost, and whether retrieval errors introduce new failure modes. |

All three configurations will be trained/evaluated using the same base
classification architecture where feasible, so that observed differences are
attributable to the input context strategy rather than to confounded model
differences. Where architectural constraints make this infeasible (e.g.,
input length limits require different handling across configurations), the
discrepancy and its justification will be documented explicitly alongside
results.

## 9. Candidate baseline and transformer approaches

Model selection is **provisional** and will not be finalized until the
dataset audit and literature review (tracked separately in
[`PROJECT_STATUS.md`](../../PROJECT_STATUS.md)) are complete. The following
are candidate approaches under consideration, listed for planning purposes
only:

**Baseline (non-neural) candidates:**
- TF-IDF or bag-of-words features with a linear classifier (logistic
  regression / linear SVM), run on configuration A only, to establish a
  cheap, interpretable lower bound.

**Transformer-based candidates:**
- Pretrained encoder models (e.g., BERT-family or similarly sized
  open-weight encoders) fine-tuned for sequence-pair classification, taking
  `(policy_context, comment)` as a pair input for configurations B and C.
- Pretrained sentence/document embedding models for the retrieval step in
  Section 7 (separate from the classification model itself).

**Selection criteria to be applied once the literature review and dataset
audit are complete:**
- Compatibility with CPU execution and the 8 GB RAM development constraint
  stated in the project README, with GPU use treated as optional
  acceleration rather than a requirement.
- Open-source and freely licensed, per project constraints.
- Reasonable maximum input length for configuration B, or clear justification
  for chunking/truncation strategy if the full policy document exceeds it.
- Demonstrated prior use in stance detection or related document-grounded
  classification tasks in the literature, to be confirmed during the
  literature review rather than assumed here.

No model has been selected, downloaded, trained, or evaluated as of this
document. This section records candidates for future decision-making only.

## 10. Human annotation and quality-control requirements

- **Annotation schema:** Each eligible comment is annotated with one of the
  four stance labels (Section 4). Each comment first passes an eligibility
  check (Section 6/R6); excluded comments receive a reason code instead of
  a stance label. Multi-issue comments additionally record per-issue
  sub-judgments in the annotation tool. *(Revision 2026-11-08: the earlier
  `ambiguous` flag and "off-topic sub-reason under Neutral" are superseded
  by the Unclear label and the exclusion reason codes, respectively.)* Full
  schema detail is in
  [`docs/dataset/STANCE_ANNOTATION_GUIDELINES.md`](../../docs/dataset/STANCE_ANNOTATION_GUIDELINES.md).
- **Annotator guidelines:** Annotators will be given this document (or a
  derived annotator-facing guide) including the rule set in Section 5 and
  worked examples, before annotating any production data.
- **Multiple annotators per item:** A meaningful subset of comments (exact
  proportion to be determined based on available annotator capacity, not
  specified here) will be labeled by more than one annotator to allow
  inter-annotator agreement measurement.
- **Agreement metric:** Cohen's kappa (two annotators) or Fleiss' kappa
  (three or more annotators) will be computed overall and separately for the
  ambiguous/conditional/multi-issue subsets identified in Section 6, since
  these are expected to show lower agreement.
- **Adjudication:** Disagreements will be resolved through a defined
  adjudication process (a designated senior annotator, or majority vote
  where three or more annotators are used) rather than arbitrary
  tie-breaking. Items that cannot be confidently adjudicated even after
  review will be excluded from the gold evaluation set and logged, not
  forced into a label.
- **Annotator access to policy context:** Annotators label with full access
  to the policy document, regardless of which experimental configuration
  (Section 8) a given model run will later use. The ground truth labels
  represent the policy-aware judgment in all cases; configuration A
  (comment-only) is evaluated against the same gold labels to measure its
  shortfall, not against a separately-collected comment-only ground truth.
- **No synthetic or placeholder labels:** Per project constraints, no labels
  will be fabricated or estimated prior to actual human annotation; this
  document does not assume any annotated data exists yet.

## 11. Training, validation and testing strategy

- **Splitting unit:** Splits will be made at the **policy level**, not the
  comment level, for the primary test set — i.e., comments from a given
  policy document will not be split across train and test. This is required
  to support the unseen-policy generalization evaluation in Section 13 and
  to avoid leakage via policy-specific vocabulary or topic cues.
- **Proposed split structure (provisional, pending dataset size):**
  - A **training set** drawn from a subset of policies, used to fit model
    parameters (for transformer approaches) or feature weights (for
    baselines).
  - A **validation set**, either held out from the same policies (comment-level
    split) or from entirely separate policies, used for hyperparameter
    selection and early stopping. The choice between these two validation
    strategies will be made once literature review clarifies standard
    practice for this task type, and will be documented when finalized.
  - A **test set** held out at the policy level and used only once model
    and hyperparameter selection are finalized, to report final metrics.
- **Cross-validation:** Given the policy-level split constraint, k-fold
  cross-validation across policies (rather than a single fixed split) is a
  candidate strategy to make efficient use of a potentially limited number
  of distinct policy documents; the decision to use k-fold vs. a fixed split
  is deferred until the dataset audit establishes how many distinct policies
  are available.
- **No test-set access during development:** The test set will not be
  inspected or used for any decision-making (feature selection, model choice,
  hyperparameters, prompt design) until final evaluation, to keep reported
  numbers honest.

## 12. Evaluation metrics, including Macro-F1 and confusion matrix

Primary metrics for the four-way classification task:

- **Macro-F1** — the primary reported metric, chosen over accuracy or
  micro-F1 because stance label distribution is expected to be imbalanced
  (e.g., Neutral and Support/Oppose are unlikely to be equally frequent
  across arbitrary policies), and macro-averaging weights all four classes
  equally regardless of frequency.
- **Per-class precision, recall, and F1** — reported alongside Macro-F1 so
  that class-specific weaknesses (e.g., a model systematically confusing
  Unclear with Support/Oppose) are visible rather than hidden in an
  aggregate number.
- **Confusion matrix** — reported for every evaluated configuration, to
  characterize the specific error patterns between the four classes (e.g.,
  whether confusion concentrates on Unclear ↔ Support/Oppose boundaries
  *(Revision 2026-11-08: was Mixed)*, or on Neutral ↔ Unclear boundaries —
  since excluded comments are no longer part of the labeled set at all,
  "Neutral ↔ off-topic" confusion is now out of scope for this metric and
  is instead an exclusion-step quality question, not a label confusion).
- **Accuracy** — reported as a secondary, descriptive statistic only, given
  its known sensitivity to class imbalance.
- **Retrieval quality metrics** (for configuration C specifically) — standard
  retrieval metrics such as recall@k or precision@k against annotator-marked
  "relevant section" references, where such references are collected during
  annotation. The feasibility of collecting these references is itself
  dependent on annotation tooling design, which is out of scope for this
  document.

All metrics will be computed on the held-out test set defined in Section 11,
separately for each of the three configurations in Section 8, to allow
direct comparison. No metric values are reported in this document, as no
model has been trained or evaluated.

## 13. Unseen-policy generalization evaluation

Because PolicyLens must eventually classify comments on policies not seen
during training, generalization to unseen policies is treated as a primary
evaluation axis, not an afterthought:

- The policy-level test split (Section 11) already ensures the standard test
  metrics (Section 12) are computed on policies unseen during training.
- In addition, a dedicated **unseen-policy generalization analysis** will
  compare performance (Macro-F1 and confusion matrix) between:
  - Policies from a similar domain/topic area to those in the training set,
    and
  - Policies from a substantially different domain/topic area, if the
    eventual dataset includes enough topic diversity to support this
    comparison.
- This comparison is intended to surface whether a model is learning
  genuine policy-comment stance reasoning versus overfitting to
  topic-specific vocabulary or framing patterns seen during training. The
  specific domains/topics to be compared cannot be specified until the
  dataset audit determines what policy documents are actually available.
- If the available dataset does not contain sufficient topic diversity to
  support this analysis, that limitation will be documented explicitly
  rather than the analysis being silently skipped or substituted with a
  weaker proxy.

## 14. Known limitations and open research questions

**Known limitations of this methodology, as currently specified:**

- The four-category schema (Section 4) may not capture finer distinctions
  that could matter for downstream analysis (e.g., intensity of support/
  opposition). *(Revision 2026-11-08: the distinction between "off-topic"
  and "on-topic but no stance" — previously an open limitation here — is
  now addressed by the exclusion-code system in Section 6/R6, which
  separates excluded comments from the Neutral label entirely.)*
- Policy documents vary widely in length, structure, and formatting; the
  segmentation approach in Section 7 (structure-based with chunking
  fallback) is a provisional default, not a validated method, and may
  perform unevenly across document types.
- Conditional and multi-issue comments (Section 6) are acknowledged sources
  of lower agreement and classification difficulty; this methodology
  documents how they are handled but does not claim the handling eliminates
  the underlying difficulty.
- The approach assumes policy documents are available in machine-readable
  text form; scanned/image-based policy documents would require an OCR step
  not addressed here.

**Open research questions, to be addressed via literature review and/or
future experimentation (not in this document):**

1. Does retrieved context (configuration C) actually match full-document
   context (configuration B) in classification quality, or does retrieval
   error meaningfully degrade performance relative to full context?
2. What is the right unit of policy context for retrieval — fixed-size
   chunks, structural sections, or a learned/adaptive segmentation — and
   does the answer vary by policy document type?
3. How much annotated data, and how many distinct policies, are required
   for acceptable unseen-policy generalization (Section 13), and is this
   feasible within the project's data constraints?
4. Should comment metadata (timestamps, explicit section references, if
   present in source data) be incorporated into the model, and if so, how?
5. Is a four-way schema sufficient for the downstream semantic grouping and
   summarization stages of the PolicyLens pipeline, or does information lost
   at the stance-classification stage (e.g., intensity, specific sub-issue)
   need to be preserved for those later stages?
6. What is the appropriate treatment of sarcasm/rhetorical comments (R7) at
   scale, where manual adjudication of every ambiguous case is not feasible?

These questions are intentionally left open. This document defines the
methodology and experimental design needed to begin investigating them, not
their answers.

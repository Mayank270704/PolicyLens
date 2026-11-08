# Taxonomy Consistency Audit

**Scope:** Project-wide search and reconciliation following finalization of
the four-class stance taxonomy — **Support, Oppose, Neutral, Unclear** —
with **Mixed merged into Unclear**. This audit covers `research/`, `docs/`,
`ml/`, `configs/`, `data/`, and project root documentation.

**Method:** Recursive text search (`grep`) across all `.md`, `.csv`, and
`.json` files for `Mixed`, the old four-class phrase pattern, and related
terms, followed by manual review of every match and, for CSVs, a Python
(`csv` module, standard library only, isolated mode) check of actual label
*values* in every historical annotation file. No dependencies were
installed, no model was trained, and no git operations were run.

## 1. Search results

| File | Type | Finding | Action |
|---|---|---|---|
| `README.md` | Active project doc | Objective list said "...Neutral, or **Mixed**." | **Updated** → Unclear. |
| `research/methodology/STANCE_CLASSIFICATION_GUIDELINES.md` | Active methodology (proposed) | Entire draft built around Support/Oppose/Neutral/**Mixed**; multiple rules (R2, R4, R5, R6, R7), the taxonomy table, worked-examples table, annotation schema, and evaluation-metrics sections referenced Mixed or an off-topic→Neutral scheme inconsistent with the finalized exclusion system. | **Updated** — see Section 2 below. |
| `docs/dataset/STANCE_LABEL_DEFINITIONS.md` | Active, finalized (created prior turn) | Already correct; mentions "Mixed" only to document that it is absorbed into Unclear. | No change needed. |
| `docs/dataset/STANCE_ANNOTATION_GUIDELINES.md` | Active, finalized (created prior turn) | Already correct; one mention noting the taxonomy supersedes the old draft. | No change needed. |
| `docs/dataset/STANCE_ANNOTATION_EXAMPLES.csv` | Active, finalized (created prior turn) | Already uses only Support/Oppose/Neutral/Unclear (40 rows, 10 per label, verified). | No change needed. |
| `docs/dataset/MODEL_REGISTRY.md` | **Historical** (migrated from prior project, see [`MIGRATION_VERIFICATION_REPORT.md`](MIGRATION_VERIFICATION_REPORT.md)) | Describes a deprecated 5-class synthetic staging candidate (`Support, Oppose, Neutral, Mixed, Unclear`) from the prior project, already self-documented there as staging-only / not production-ready / superseded by a 3-class (Support/Neutral/Unclear) correction. | **Not modified.** This is a historical research record of the *previous* project's model experiments, not active PolicyLens methodology. No model has been built in the new project yet (per project constraints), so there is nothing here to reconcile against; editing it would alter a historical record of what that prior experiment actually did. |
| `docs/dataset/INFERENCE_API.md` | **Historical** (migrated, same as above) | Same deprecated 5-class staging endpoint, plus a corrected 3-class production endpoint description, both pre-existing/historical. | **Not modified**, same reasoning as above. |
| `data/processed/canonical_corpus/corpus_entries.csv`, `unique_texts.csv`, `unique_texts_labeled.csv` | Historical/raw corpus data | "Mixed" appears only inside a verbatim public comment's text ("Mixed results: informative and frustating"), not as a label or taxonomy term. In `unique_texts_labeled.csv`, this exact comment's `human_label` value is already `unclear`. | **Not modified** (per strict rule against touching historical/raw data); confirms the historical label for this comment is already consistent with the finalized taxonomy. |
| `data/raw/original_sources/*.csv` | Raw source data | "Mixed" appears only inside free-text survey responses (e.g., "Mixed-Member Proportional Representation", "Mixed results..."), unrelated to stance labeling. | **Not modified** (raw source data, out of scope and protected by strict rules). |
| `configs/`, `ml/` | Active, empty scaffolding | Contain only `.gitkeep` placeholders; no label or taxonomy references exist. | No change needed. |
| `PROJECT_STATUS.md` | Active project doc | Contains no label-specific text (references the methodology document by link only). | No change needed. |

No matches were found for "old label mappings" or "outdated classification examples" beyond what is listed above — the worked-examples table in the research methodology document (Section 5.3) was the only other place carrying an outdated example, and is covered in Section 2 below.

## 2. Documentation updated

### `research/methodology/STANCE_CLASSIFICATION_GUIDELINES.md`

This document was **updated in place**, not deleted or replaced, with inline
`**Revision (2026-11-08):**` markers at every point where the finalized
taxonomy changed a rule's outcome (not just a label's name), so the fact and
nature of each change remains visible in the document itself:

- Added a revision notice at the top pointing to the three authoritative
  `docs/dataset/` files as the now-canonical source for definitions, rules,
  workflow, and examples; this document remains the research-methodology
  record (experimental configurations, model candidates, training/
  evaluation strategy).
- **Section 1:** label set in the formal notation updated to
  `{Support, Oppose, Neutral, Unclear}`.
- **Section 2:** updated the Support/Oppose/Neutral/Mixed phrase and added a
  note that off-topic comments are now excluded, not labeled.
- **Section 4:** replaced the Mixed row with the finalized Unclear
  definition; rewrote the paragraph that previously said off-topic comments
  are "captured under Neutral rather than excluded" — this is now the
  opposite of the finalized methodology, so it was corrected to describe
  the exclusion-code system instead.
- **Section 5.2:**
  - R2: "split direction → Mixed" → "→ Unclear."
  - R4: "push the label toward Mixed" → "toward Unclear"; added the
    implementation-vs-substance test (the finalized guidelines' rule that
    implementation criticism is not automatically disqualifying) which the
    original draft did not have.
  - R5: narrowed to cover only comments with *no* evaluative attempt
    (Neutral); vague-but-engaged comments are now explicitly routed to
    Unclear instead of Neutral — the original draft conflated these two.
  - R6: rewritten from "Off-topic → Neutral" to "Off-topic/spam/non-
    substantive/unintelligible → **excluded**, not labeled," matching the
    finalized exclusion-code system.
  - R7: sarcasm default changed from Neutral to Unclear.
- **Section 5.3:** worked-examples table's Mixed row relabeled Unclear;
  added a pointer to the finalized 40-row examples CSV.
- **Section 6:** rewrote the "ambiguous comments" bullet (previously
  Neutral + an `ambiguous=true` tooling flag; now directly labeled
  Unclear) and added a new bullet describing the exclusion workflow, which
  this section previously did not separate from "ambiguous."
- **Section 10:** rewrote the annotation-schema bullet to remove the
  outdated `ambiguous` flag and "off-topic sub-reason under Neutral,"
  replacing both with a reference to the finalized exclusion codes and
  the Unclear label.
- **Section 12:** updated the per-class and confusion-matrix metric
  descriptions from "Mixed" to "Unclear," and corrected the confusion-
  matrix example since "Neutral ↔ off-topic" is no longer a label-confusion
  question once off-topic comments are excluded before labeling.
- **Section 14:** marked the "off-topic vs. on-topic-but-no-stance"
  limitation as resolved by the Section 6/R6 exclusion system, rather than
  leaving it listed as an open limitation.

### `README.md`

Updated the one-line objective statement ("...Neutral, or Mixed") to
"...Neutral, or Unclear."

## 3. Verification

| Check | Result |
|---|---|
| Exactly four active stance labels exist | **Confirmed.** Support, Oppose, Neutral, Unclear — consistently defined across `STANCE_LABEL_DEFINITIONS.md`, `STANCE_ANNOTATION_GUIDELINES.md`, `STANCE_ANNOTATION_EXAMPLES.csv`, and (after this update) `research/methodology/STANCE_CLASSIFICATION_GUIDELINES.md` and `README.md`. |
| Mixed maps to Unclear | **Confirmed.** Documented explicitly in `STANCE_LABEL_DEFINITIONS.md` (rule D5) and now in the research methodology document's revision notes; no document asserts Mixed as a live, separate label. |
| Exclusion codes are not stance labels | **Confirmed.** `SPAM`, `OFF_TOPIC`, `TOO_SHORT_NONSUBSTANTIVE`, `UNINTELLIGIBLE` are documented as a pre-labeling eligibility decision (rule D8 / R6) in both `docs/dataset/STANCE_ANNOTATION_GUIDELINES.md` and the updated research methodology document; a comment that is excluded receives a reason code, never one of the four stance labels. |
| Historical annotation labels remain unchanged | **Confirmed.** No historical annotation CSV was modified. A Python read-only check of label *values* (not just text search) in `consolidated_stance_dataset.csv`, `consolidated_stance_dataset_corrected.csv`, `stance_human_gold_400_provisional.csv`, `stance_targeted_master.csv`, and `stance_targeted_reviewer_blind.csv` found every existing label is already one of `Support`/`Oppose`/`Neutral`/`Unclear` (case varies by file) — **no `Mixed` label value exists anywhere in the historical annotation data.** This is a pre-existing property of that data, not a result of this audit. |
| No conflicting active methodology remains | **Confirmed**, with one noted exception kept out of scope — see Section 4. |

## 4. Unresolved items / out-of-scope findings

- **`docs/dataset/MODEL_REGISTRY.md` and `docs/dataset/INFERENCE_API.md`**
  still describe a deprecated 5-class scheme (`Support, Oppose, Neutral,
  Mixed, Unclear`) as part of the *prior* project's historical experiment
  record. This is **not a live conflict** with the current PolicyLens
  methodology — no model exists yet in the new project to be inconsistent
  with anything — but it is flagged here for visibility. These files were
  intentionally left unmodified because they are historical records of a
  different (predecessor) project's completed work, already migrated and
  hash-verified in `MIGRATION_VERIFICATION_REPORT.md`, and the task's strict
  rules prohibit treating migrated historical research records as something
  to rewrite. If a future task wants these files annotated with an explicit
  "superseded / historical reference only, predates current taxonomy"
  banner (similar to what their own text already partially states), that
  would be a separate, explicitly scoped documentation task.
- No other unresolved conflicts were found.

## 5. Files modified by this audit

- `research/methodology/STANCE_CLASSIFICATION_GUIDELINES.md` (updated in
  place; taxonomy finalized, rules reconciled with the finalized exclusion
  system; no content deleted, all changes marked inline with revision
  notes).
- `README.md` (one-line taxonomy correction).
- `docs/dataset/TAXONOMY_CONSISTENCY_AUDIT.md` (this report, new file).

No other files were modified. No historical annotation CSVs, migrated
historical documentation, raw/processed data files, models, or git state
were touched.

# Stance Annotation Guidelines

**Status:** Finalized annotation methodology for the PolicyLens four-class
policy stance classification system. This document governs how human
annotators label public comments against a policy document. It assumes the
label taxonomy and decision rules in
[`STANCE_LABEL_DEFINITIONS.md`](STANCE_LABEL_DEFINITIONS.md) (read that
file first) and is illustrated by
[`STANCE_ANNOTATION_EXAMPLES.csv`](STANCE_ANNOTATION_EXAMPLES.csv).

This document describes **methodology only**. No comments have been
annotated, no historical annotation data has been modified, and no model
has been trained as a result of this document.

## 1. Scope and relationship to other documents

- **Label taxonomy and decision rules:** [`STANCE_LABEL_DEFINITIONS.md`](STANCE_LABEL_DEFINITIONS.md).
- **Worked examples:** [`STANCE_ANNOTATION_EXAMPLES.csv`](STANCE_ANNOTATION_EXAMPLES.csv), at least 10 examples per label including borderline cases, each citing the decision rule it illustrates.
- **This document:** the annotation workflow, annotator instructions, disagreement handling, adjudication procedure, exclusion criteria, policy-context requirements, and common mistakes.

This taxonomy (Support / Oppose / Neutral / Unclear) is the **final** label
set for the current PolicyLens implementation. It supersedes the
Support/Oppose/Neutral/**Mixed** draft in the earlier research methodology
document; see the note at the top of `STANCE_LABEL_DEFINITIONS.md`.

## 2. Policy-context requirements

Annotators label comments **against a specific policy document**, not in
the abstract.

- Every annotation session is scoped to one policy. Annotators must have
  the full policy document (or the relevant section(s), at minimum)
  available and open while labeling — not labeling from memory of having
  skimmed it earlier.
- Per rule D6, whenever a comment references a specific provision, clause,
  numeric threshold, section, or defined term, the annotator must locate
  and read that part of the policy document before assigning a label. If
  the comment's claim about the policy is inaccurate (e.g., misquotes a
  threshold), label the commenter's **expressed stance toward the policy as
  they understood it**, not a correction of their facts — annotators are
  not fact-checking comments, only determining stance.
- If a policy is long, annotators may use a provided section index or
  table of contents to navigate directly to the relevant provision rather
  than reading the full document for every comment. The annotation tool
  should make the current section easy to jump to (a tooling requirement,
  not specified further here).
- If a comment does not reference any specific provision and is evaluable
  from its general content plus the policy's overall stated purpose, full
  re-reading of the document is not required — but annotators must still
  know, at minimum, what the policy's core proposal is.

## 3. Annotation workflow

For each comment, in order:

1. **Eligibility check (exclusion pass).** Before considering stance at
   all, determine whether the comment should be excluded under
   [Section 5](#exclusion-criteria). If excluded, record the exclusion
   reason code and **stop** — do not assign a stance label.
2. **Read the comment in full.** Do not label from a truncated preview.
3. **Identify what the comment references.** Note any specific provisions,
   sections, or thresholds mentioned. If present, consult the policy
   document per [Section 2](#policy-context-requirements) (rule D6).
4. **Determine evaluative direction, not tone (D1).** Ask: is the
   commenter, on balance, for or against the policy as proposed — setting
   aside how they said it?
5. **Check for provision-level vs. whole-policy scope (D2).** If the
   comment addresses one specific part, determine whether the commenter
   generalizes to the whole policy, and whether a net direction can still
   be determined.
6. **Check for conditional framing (D3).** If the comment is conditional,
   determine whether the condition reflects what the policy already does,
   a core objection, a minor caveat, or genuine unresolved ambiguity.
7. **Check for implementation vs. substance framing (D4).** If the comment
   criticizes execution/rollout, apply the "would the position flip if
   the concern were resolved?" test.
8. **Decide: can a single net direction be assigned?**
   - Yes, favourable → **Support**.
   - Yes, unfavourable → **Oppose**.
   - No direction at all (question, fact, statement of relevance) →
     **Neutral**.
   - No — genuinely balanced, contradictory, or indeterminate even with
     full context (D5) → **Unclear**.
9. **Record the label plus supporting notes.** Annotators record a short
   free-text justification (one sentence) for every label, referencing
   which decision rule(s) applied when the case was non-trivial. This is
   required for all Unclear and Oppose-via-D4 labels, and encouraged for
   the rest.
10. **Flag for adjudication if confidence is low.** Annotators may mark any
    item "needs review" regardless of which label they assigned, not only
    Unclear ones.

## 4. Annotator instructions

- **Label the comment, not the commenter.** Do not use information about
  who submitted a comment (affiliation, past comments, tone of other
  submissions) to influence the label of the current comment.
- **One policy at a time.** Do not carry assumptions from one policy's
  annotation session into another; each policy may use similar language
  differently.
- **Do not skim.** Comments that reference specific clauses require the
  policy text open, per [Section 2](#policy-context-requirements).
- **Do not guess silently.** If a label isn't confident, write the
  justification note explaining the uncertainty and flag for adjudication
  rather than picking a label and moving on.
- **Multiple annotators per item.** A defined subset of comments (exact
  proportion determined by annotator capacity, not fixed in this document)
  is labeled independently by two or more annotators, without seeing each
  other's labels, to support the disagreement handling in
  [Section 6](#disagreement-handling).
- **No label changes outside the documented workflow.** Once submitted, an
  annotator's label is not self-edited silently; corrections go through
  adjudication (Section 7) so the change is tracked.
- **Historical data is read-only.** Previously collected annotations from
  prior research phases are reference material for calibration only. They
  are not to be edited, relabeled, or overwritten as part of this
  methodology's rollout.

## 5. Exclusion criteria

Per rule D8, some comments are excluded from stance labeling entirely
rather than forced into one of the four labels — including Neutral, which
is reserved for on-topic comments with no clear direction, not for comments
that shouldn't be evaluated at all.

| Reason code | Definition | Example |
|---|---|---|
| `SPAM` | Promotional, automated, or clearly unrelated bulk content. | "Buy cheap watches at [link]" |
| `OFF_TOPIC` | Comment does not discuss the policy or any related subject matter at all. | "When is the city fixing potholes on Elm Street?" submitted on a transit-fare policy with no connection drawn to the policy. |
| `TOO_SHORT_NONSUBSTANTIVE` | Contains no evaluable content — too brief or generic to support any stance determination, as opposed to being vague-but-substantive (which is Unclear; see Section 8). | "ok", "test", "n/a", a single punctuation mark. |
| `UNINTELLIGIBLE` | Garbled, corrupted, or not resolvable into coherent language (encoding errors, keyboard mashing). | "asdkjf ##@@ 3993" |

Rules for applying exclusion:

- Exclusion is decided **before** any stance reasoning. If a comment is
  excluded, no label is recorded.
- Exclusion reason codes are mutually exclusive; pick the single best fit.
- A comment that is merely **short but substantive** (e.g., "No, too
  expensive.") is **not** excluded — it is a valid, if brief, Oppose. Length
  alone is not disqualifying; absence of evaluable content is.
- A comment that is **on-topic but vague** (e.g., "This policy is
  complicated.") is not `TOO_SHORT_NONSUBSTANTIVE` — it is **Unclear**
  (insufficient information), because it engages with the policy but
  doesn't commit to a direction. See the Neutral/Unclear/Exclusion
  distinction in [Section 8](#common-annotation-mistakes).
- Excluded comments are still retained in the dataset with their exclusion
  code recorded (per the project's constraint to preserve all original
  comments) — exclusion affects stance labeling only, not data retention.

## 6. Disagreement handling

- **Agreement measurement.** For comments labeled by two annotators,
  compute Cohen's kappa; for three or more, Fleiss' kappa. Report overall
  agreement and, separately, agreement restricted to comments involving
  D2–D5 (provision-scope, conditional, implementation, or mixed/conflicting
  cases), since these are expected to show lower agreement than
  straightforward Support/Oppose calls.
- **Disagreement is not an error state.** Divergent labels on a genuinely
  hard case are expected and valuable signal about where the taxonomy or
  guidelines need sharpening — they are logged for review, not treated as
  one annotator being "wrong" by default.
- **Systematic disagreement patterns.** If agreement is consistently low
  for a specific rule (e.g., many D4 implementation-criticism cases
  disagree), this is flagged as a guideline issue, not just re-adjudicated
  case by case — see [Section 8](#common-annotation-mistakes) for the kind
  of systematic errors this surfaces.

## 7. Adjudication procedure

1. Any comment with annotator disagreement, or flagged "needs review" by
   any annotator, enters the adjudication queue.
2. A designated senior annotator (or, where three or more initial
   annotators were used, majority vote) reviews the comment, the policy
   context, and each annotator's justification note.
3. The adjudicator either confirms one of the existing labels or assigns a
   different one, and records a justification referencing the applicable
   decision rule(s).
4. If the adjudicator cannot confidently resolve the case even with full
   context, the final label is **Unclear**, with a note explaining that
   the comment was adjudicated-but-indeterminate (this is a legitimate,
   expected outcome, not a failure of adjudication).
5. Adjudication decisions are logged with: comment ID, original label(s),
   final label, adjudicator, and justification — so that the final gold
   dataset is auditable back to a reasoned decision for every contested
   case.
6. Adjudicators do not re-adjudicate their own initial labels; a different
   person performs adjudication than any of the item's original
   annotators, where staffing allows.

## 8. Common annotation mistakes

Documented so annotators and reviewers can self-check against them:

1. **Treating emotional tone as the label.** Labeling an angry comment
   Oppose or a cheerful comment Support without checking the actual
   argument's direction (violates D1).
2. **Letting one bad provision sink the whole label.** Reading any
   criticism at all as Oppose, even when the commenter's overall framing
   is clearly net-favourable (violates D2).
3. **Defaulting conditional comments to Unclear.** Conditional support/
   opposition is not automatically Unclear — only when the condition's
   resolution is genuinely unknown (violates D3; see
   `STANCE_LABEL_DEFINITIONS.md`).
4. **Equating any implementation complaint with Oppose.** A comment that
   supports the policy's goal but worries about execution is still
   Support, not Oppose, unless the complaint is actually about substance
   (violates D4).
5. **Overusing Unclear as a "not sure" dump.** Unclear is for comments
   that are *genuinely* balanced or indeterminate, not a convenient label
   for anything an annotator finds mildly ambiguous after a quick read.
   Re-read the comment and apply D1–D4 before defaulting to Unclear.
6. **Confusing Neutral with Unclear.** Neutral = clearly no direction
   (question, fact). Unclear = a direction may exist but can't be
   resolved. A pure clarifying question is Neutral, not Unclear.
7. **Confusing exclusion with Neutral.** An off-topic or spam comment is
   **excluded**, not labeled Neutral. Neutral requires the comment to
   actually engage with the policy.
8. **Confusing exclusion with Unclear.** A vague but on-topic comment
   ("this is complicated") is Unclear, not `TOO_SHORT_NONSUBSTANTIVE`.
   Exclusion is for comments with no evaluable content at all, not for
   genuinely ambiguous ones.
9. **Skipping policy context for provision-specific comments.** Labeling a
   comment that cites a specific clause or number without opening the
   policy document to check what that clause/number actually says
   (violates D6).
10. **Guessing on unresolved sarcasm.** Forcing Support or Oppose on
    sarcastic comments whose target is genuinely ambiguous, instead of
    flagging as Unclear per D7.
11. **Carrying bias from the commenter's identity or history.** Using
    anything other than the comment's own text and the policy context to
    determine its label.

## 9. Relationship to historical annotation data

Prior research-phase annotation artifacts (e.g., the consolidated stance
dataset and targeted annotation samples referenced in
[`MIGRATION_VERIFICATION_REPORT.md`](MIGRATION_VERIFICATION_REPORT.md)) used
an earlier label set and guideline version. This document does not modify,
relabel, or reconcile those historical files. Any future decision to
re-annotate or map historical labels onto this finalized taxonomy is a
separate, explicitly scoped task.

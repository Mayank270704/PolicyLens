# Stance Label Definitions

**Status:** Final label taxonomy for the PolicyLens annotation methodology.
This document defines the four output labels and the decision rules used to
resolve the hard cases between them. It is the normative reference for
[`STANCE_ANNOTATION_GUIDELINES.md`](STANCE_ANNOTATION_GUIDELINES.md) and
[`STANCE_ANNOTATION_EXAMPLES.csv`](STANCE_ANNOTATION_EXAMPLES.csv).

This taxonomy supersedes the earlier four-category draft
(Support/Oppose/Neutral/**Mixed**) referenced in
[`research/methodology/STANCE_CLASSIFICATION_GUIDELINES.md`](../../research/methodology/STANCE_CLASSIFICATION_GUIDELINES.md).
In this finalized taxonomy, **Mixed is not a separate label** — it is folded
into **Unclear** (see D5 below). The research methodology document has not
yet been updated to reflect this change; treat this file as authoritative
for annotation going forward.

## The four output labels

There are **exactly four** output labels. Every comment that is eligible for
stance labeling (i.e., not excluded — see
[Exclusion criteria](STANCE_ANNOTATION_GUIDELINES.md#exclusion-criteria))
receives exactly one of them.

| # | Label | Definition |
|---|---|---|
| 1 | **Support** | The commenter expresses agreement, approval, or a favourable position toward the policy. |
| 2 | **Oppose** | The commenter expresses disagreement, rejection, or an unfavourable position toward the policy. |
| 3 | **Neutral** | The commenter asks questions, provides information, or discusses the policy without expressing a clear favourable or unfavourable position. |
| 4 | **Unclear** | Covers: mixed opinions containing both support and opposition; conflicting positions; insufficient information to determine stance; and comments whose stance cannot be confidently established even with full policy context. |

**Neutral vs. Unclear, at a glance:** Neutral is a comment that clearly
*has no evaluative direction* (a question, a fact, a statement of personal
relevance) — there is nothing ambiguous about it; it simply isn't taking a
side. Unclear is a comment where a direction *might* exist, or *parts of* a
direction exist, but it cannot be resolved into one confident label — either
because it genuinely pulls both ways, or because there isn't enough content
to tell. Confusing these two is one of the most common annotation errors
(see [Common annotation mistakes](STANCE_ANNOTATION_GUIDELINES.md#common-annotation-mistakes)).

## Decision rules (D1–D8)

These rules resolve the specific hard cases called out in the project's
annotation requirements. Each example in
[`STANCE_ANNOTATION_EXAMPLES.csv`](STANCE_ANNOTATION_EXAMPLES.csv) cites the
rule(s) it illustrates by code.

### D1 — Direction over tone

Classify by the evaluative **direction** of the comment (for/against the
policy), not by its emotional tone, politeness, or intensity. A calm,
reasoned comment can be a clear Oppose; an angry or sarcastic comment can be
a clear Support. Tone is evidence to interpret, never the label itself.

### D2 — Provision-level criticism vs. whole-policy rejection

A comment may criticize or praise **one specific provision** of a policy
without that automatically determining the label for the **policy as a
whole**. Annotators must distinguish:

- Criticism/praise of *one part*, with the rest of the comment's framing
  leaving the overall position toward the policy clearly net-favourable or
  net-unfavourable → label by the **net** direction (Support or Oppose).
- Criticism/praise of one part **explicitly generalized** by the commenter
  into rejection or endorsement of the whole policy ("this specific plan is
  a non-starter," "overall, this is the right call") → label by that
  explicit overall statement.
- Genuinely split positions across multiple provisions with **no
  resolvable net direction**, especially where the commenter does not
  attempt to weigh one against the other → **Unclear** (see D5).

### D3 — Conditional statements

A conditional comment ("I'd support this if X," "I oppose this unless Y")
is evaluated by its **net direction toward the policy as actually
proposed**, not toward the commenter's hypothetical preferred version:

- If the condition **is what the policy already does** (the commenter is
  affirming a provision that's actually in the proposal), this is Support
  or Oppose, not a caveat to discount.
- If the condition is **a core objection to the policy as written** (the
  commenter rejects a central provision unless it changes), the net
  direction is Oppose, not Unclear.
- If the condition is **minor** relative to an otherwise clear position,
  the minor caveat does not change the label (see D4).
- **Conditional support is not automatically Unclear.** Only classify a
  conditional as Unclear when the condition's resolution is genuinely
  unknown or unspecified by the policy itself, such that no annotator
  could determine a net direction even with full policy context (e.g., the
  commenter's position depends on a detail the policy document does not
  state).

### D4 — Implementation criticism vs. substantive rejection

**Do not automatically classify criticism of implementation as Oppose.**
Distinguish:

- Criticism of **execution, logistics, timeline, funding, communication,
  or follow-through** ("I hope they actually deliver this," "the rollout
  should start sooner") while the policy's substance/goal is still
  endorsed → the core position stands; usually **Support** (or Oppose, if
  the substance was rejected to begin with) with the implementation concern
  noted but not label-determining.
- Criticism that targets the policy's **core applicability, scope, or
  substance** — even when framed as an implementation complaint — should
  be read for what it actually rejects. "This can't work because the
  mandate applies to situations where it fundamentally doesn't make sense"
  is a substantive objection, not a logistics complaint, and supports
  **Oppose**.

The test: *if the implementation concern were fully resolved, would the
commenter's position flip?* If yes, the concern is about the policy's
substance (weigh accordingly). If no — they'd still feel the same way about
the policy itself — the concern is about execution and does not override
the underlying direction.

### D5 — Mixed and conflicting positions → Unclear

There is no separate "Mixed" label. A comment is labeled **Unclear** (not
Mixed, not split into two labels) when:

- It expresses **genuinely balanced** support and opposition that the
  commenter does not resolve to a net direction (e.g., "I don't know which
  matters more").
- It contains **explicit self-contradiction** ("this is exactly what we
  need and exactly what will ruin the neighborhood").
- It splits across **many provisions** with no coherent aggregate position,
  especially when the commenter states they cannot form an overall view.

Contrast with D2/D4: if a net direction *can* be determined despite a
caveat or provision-specific criticism, use Support/Oppose, not Unclear.
Unclear is for cases that **cannot** be resolved to a net direction, not a
default for "this comment has more than one idea in it."

### D6 — Policy-context requirement

When a comment references specific provisions, numeric thresholds, clauses,
section numbers, or terms defined by the policy, annotators **must consult
the relevant policy document/section** before assigning a label. A comment
cannot be correctly labeled by its surface sentiment alone when its meaning
depends on what the policy actually says (see
[Policy-context requirements](STANCE_ANNOTATION_GUIDELINES.md#policy-context-requirements)).

### D7 — No inference from emotion or sentiment alone

Do not infer stance from emotional register, sarcasm, or affect by itself.
Sarcasm and rhetorical framing must be resolved to their **intended
direction** using full context. If the intended direction genuinely cannot
be determined even with full policy context — for example, sarcasm whose
target is ambiguous between the policy itself and an unrelated claim about
it — do not guess: label **Unclear** and flag for adjudication review
rather than forcing Support or Oppose.

### D8 — Exclusion precedence

Before any of D1–D7 are applied, every comment passes an **eligibility
check**. Spam, content wholly unrelated to the policy, comments too short
or non-substantive to evaluate, and unintelligible/garbled text are
**excluded** under documented exclusion rules — they are not forced into
one of the four stance labels, including Neutral. Only comments that pass
the eligibility check are assigned Support, Oppose, Neutral, or Unclear.
Full exclusion criteria and reason codes are defined in
[`STANCE_ANNOTATION_GUIDELINES.md`](STANCE_ANNOTATION_GUIDELINES.md#exclusion-criteria).

## Summary table: which rule to reach for

| Situation | Rule |
|---|---|
| Comment is angry/sarcastic/calm but direction is still clear | D1 |
| Comment criticizes/praises one provision only | D2 |
| Comment says "I'd support/oppose this if…" | D3 |
| Comment criticizes how the policy will be rolled out/enforced | D4 |
| Comment genuinely can't be resolved to one direction | D5 |
| Comment references a specific clause, number, or section | D6 |
| Comment's tone is strong but literal direction is ambiguous (e.g. sarcasm) | D7 |
| Comment is spam, off-topic, too short, or unintelligible | D8 |

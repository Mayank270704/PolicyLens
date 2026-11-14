# Proposed Stance Protocol Clarifications — v6 (candidate)

**Status: PROPOSAL v6 — candidate, not adopted.** v6 revises
[v5](PROPOSED_STANCE_PROTOCOL_CLARIFICATIONS_v5.md) to incorporate three
methodological positions **confirmed by the reviewer in the v6 review**
(labelled **V6-R1**, **V6-R2** and **V6-R3**):
- **V6-R1:** target-less Q14 evaluations become an explicit, narrow
  exception within C1;
- **V6-R2:** a four-way split — hedged delivery uncertainty, definite
  future non-delivery, established past/present non-delivery, and
  ineffectiveness despite implementation;
- **V6-R3:** the `U-CONTEXT` and bare-agreement position is kept,
  including why the exclusion rests on evidence, not length.

Reviewer confirmation settles these positions for drafting. **It does not
adopt them.** No decision is APPROVED, and the decision register's
statuses are unchanged from v5 (see "Change log: v5 → v6"). Everything
else is carried over from v5 unchanged.

v5 revised [v4](PROPOSED_STANCE_PROTOCOL_CLARIFICATIONS_v4.md) on three
findings, labelled R1–R3 in v5 and kept with those labels below:
- R1, handling Q14 answers that name no target;
- R2, delivery doubt versus ineffectiveness;
- R3, the minimum signal for `U-CONTEXT`.

See "Change log: v4 → v5".

v4 itself revised [v3](PROPOSED_STANCE_PROTOCOL_CLARIFICATIONS_v3.md)
against the independent v3 audit (findings X1–X4, F1–F5c, O1–O6).
[v1](PROPOSED_STANCE_PROTOCOL_CLARIFICATIONS.md),
[v2](PROPOSED_STANCE_PROTOCOL_CLARIFICATIONS_v2.md), v3, v4 and v5 are
kept unchanged for the record.

This proposal changes **no authoritative document and no data**. It does
not change:
- [`STANCE_LABEL_DEFINITIONS.md`](STANCE_LABEL_DEFINITIONS.md),
  [`STANCE_ANNOTATION_GUIDELINES.md`](STANCE_ANNOTATION_GUIDELINES.md),
  [`SINGLE_ANNOTATOR_PROTOCOL.md`](SINGLE_ANNOTATOR_PROTOCOL.md) or
  `STANCE_ANNOTATION_EXAMPLES.csv`;
- any annotation, the annotation state, the repeat files or the splits;
- the models, the code or the schemas.

Those stay authoritative until a change is formally adopted. **Two
proposed rules would change the meaning of existing labels** — Decisions L
and N, described in the next section. Both need explicit approval, followed
by edits to the authoritative documents listed there.

**Evidence source:** [`../experiments/LEVEL1_ERROR_ANALYSIS.md`](../experiments/LEVEL1_ERROR_ANALYSIS.md)
(train + validation only, n = 213). Counts are analyst groupings that mark
**candidates for review**, not labels known to be wrong.

**Examples:** every example is hypothetical, written for this document, and
not taken from the annotation data.

## Decision status

| Status | Meaning |
|---|---|
| **APPROVED** | Formally adopted. **No decision has this status.** |
| **REVIEWER-DIRECTED** | A position the reviewer specified in a review instruction (v2, v3 or v4 review). Settled for drafting; adopted only with the proposal. |
| **RECOMMENDED** | Designed by the drafter. An open decision needing formal approval. |
| **OPTIONAL / DEFERRED** | Not needed for adoption. May be taken up later as a separate decision. |

Decisions A–K keep exactly the statuses set in the v3 review. New decisions
L–V cover the rules that had no status before (X4). A rule is
REVIEWER-DIRECTED only where a review instruction specified the position
itself. Details the drafter designed to implement that position are
RECOMMENDED. Every substantive rule's status is listed in the **Rule status
coverage** table near the end.

---

## Definition changes requiring explicit approval (X1, X2)

The four stance classes (Support / Oppose / Neutral / Unclear) and the four
exclusion codes are preserved: **no class or code is added or removed**
(Decision K). However, two class or code **boundaries are redefined**:

### Decision L — the Unclear/Neutral boundary is redefined (REVIEWER-DIRECTED)

- **Current definition:** Unclear includes "insufficient information to
  determine stance" and cases where "a direction *might* exist… or there
  isn't enough content to tell".
- **Proposed (C1):** Unclear requires **identifiable evaluative content
  whose direction or target can't be resolved**. In-scope comments with no
  identifiable evaluation become **Neutral**. Comments that don't engage
  with the target at all get an exclusion code.
- **Consequence:** under the current definitions, many v1 Unclear labels
  of the "insufficient information" kind are **correct**. Moving them to
  Neutral is a consequence of Decision L, not a correction of annotator
  error.

### Decision N — the OFF_TOPIC boundary is redefined (RECOMMENDED)

- **Current definition:** `OFF_TOPIC` = "does not discuss the policy or
  any related subject matter **at all**".
- **Proposed (C1, C2):** a subject is in scope only with an openness,
  transparency, accountability or participation angle (or as the
  engagement process, under Decision A). Related government policy without
  such an angle becomes `OFF_TOPIC`.
- **Consequence:** this is broader than the "at all" wording. It
  operationalises a definition that is vague in practice, but it is a
  change.

### Authoritative texts that would need future amendment if L, N or B is adopted

None is modified by this proposal.

| Document | Passage | Affected by |
|---|---|---|
| `STANCE_LABEL_DEFINITIONS.md` | L29 (Unclear row); L31–38 ("Neutral vs. Unclear, at a glance") | L |
| `STANCE_LABEL_DEFINITIONS.md` | D4, L92–114: add the corpus-specific application of D4 and the hope/doubt rule | B |
| `STANCE_LABEL_DEFINITIONS.md` | D7, L143–151: add the plausible-scope note (C1 step 1) | M |
| `STANCE_ANNOTATION_GUIDELINES.md` | §3 step 8, L77–83 ("No direction at all" / "indeterminate") | L |
| `STANCE_ANNOTATION_GUIDELINES.md` | §3 step 10, L89–91 (the needs-review flag → C9 convention) | J |
| `STANCE_ANNOTATION_GUIDELINES.md` | §5 OFF_TOPIC row, L129; exclusion rules, L133–148, including the "on-topic but vague → Unclear" bullet at L141–145 | N, L |
| `STANCE_ANNOTATION_GUIDELINES.md` | §8 common mistakes 5–8, L208–221 | L |
| `STANCE_ANNOTATION_GUIDELINES.md` | §5 `TOO_SHORT_NONSUBSTANTIVE` row, L130: clarify that bare agreement with unavailable content has no evaluable content (R3) | H |
| `SINGLE_ANNOTATOR_PROTOCOL.md` | §5, L274–277 (unexplained specific reference → "Unclear / needs-review"); also the `U-CONTEXT` minimum signal (R3) | L, J, H |
| `SINGLE_ANNOTATOR_PROTOCOL.md` | §6, L292 (note requirements); §6.2, L311–324 (confidence scale, plus the interim marker) | H, J |
| `STANCE_ANNOTATION_EXAMPLES.csv` | Unclear examples **UNC-03** (on-topic but too vague) and **UNC-08** (insufficient information) would become Neutral or need replacing | L |
| `STANCE_ANNOTATION_EXAMPLES.csv` | Re-check the Oppose and Support examples for C4 consistency and the Neutral examples for C1. Not inspected in detail here. | B, L, N |

Checked and needing no change: the annotation GUI (`scripts/annotation/gui.py`)
contains no label definitions; it only checks that Unclear labels have a
note. `REPEAT_ANNOTATION_PROCEDURE.md` defines no label boundaries.

---

## C1. Scope, OFF_TOPIC, Neutral and Unclear

**Ambiguity found.**
- Of 66 v1 Unclear labels, the notes describe 22 as unconnected to open
  government and 35 as expressing no position. About 6 describe an
  unresolvable direction or target, 2 a missing referenced context, and
  none explicitly describes balanced support and opposition (D5).
- The "no position" wording also appears in 21 of 45 Neutral notes.
- `OFF_TOPIC` was never used.

**Why it matters.** The same rationale produces different labels, and the
current Unclear class mixes off-topic, no-evaluation and genuinely
ambiguous comments.

**Proposed operational rule** — apply in order, stopping at the first
match.

**Step 1 — Scope (Decisions M, N).** Judge scope against the C2 stance
target, not the prompt's wording and not "government" in general.
- A comment has a **plausible in-scope reading** when some part of it can
  reasonably be read as addressing the target. That can come from its own
  words, or from the prompt identifying the referent of an otherwise
  target-less evaluation (C2 prompt rule). For the target-less Q14
  exception only (step 5, V6-R1), it comes from the Open Government
  questionnaire context (C7). That reading is plausible but unresolved,
  which is why those answers go to `U-TARGET` and are never `OFF_TOPIC`.
- **Uncertain target scope (F1).** Sometimes a comment contains an
  evaluation, the annotator can't tell whether its target is in scope, and
  at least one plausible reading is in scope. In that case, **proceed as in
  scope**. The comment then goes to step 3 if its target and direction
  resolve, or to step 5 (`U-TARGET (target)`) if the target stays
  unresolved. This follows D7: an ambiguous target is Unclear, not
  `OFF_TOPIC`.

**Step 2 — OFF_TOPIC.** Only when **no part** of the comment has a
plausible in-scope reading.
- The strength of an opinion never brings an unrelated subject into scope.
- **Partial scope (F5a).** If some parts are in scope and others are
  clearly not, label **from the in-scope parts only**. Out-of-scope parts
  contribute no evaluations to step 3 or to C4 dominance. The note records
  `partial scope (C1): ignored <topic>`.

**Step 3 — Support / Oppose.** In-scope evaluative content with a
resolvable net direction. This includes:
- recommendations (C3);
- implicit opposition and the C4 a–d tree;
- resolvable sarcasm (C5).

**Step 4 — Neutral (Decision L).** In-scope content with **no
identifiable evaluation** of the target. Examples: questions, information
requests, facts, personal experience, bare in-scope topics, and
announcements or thanks that refer to the target.
- **Neutral requires engaging with the target (O2).** A greeting, thanks
  or social remark that refers to nothing in scope gets the appropriate
  exclusion code, usually `TOO_SHORT_NONSUBSTANTIVE` (guidelines §8,
  mistake 7).

**Step 5 — Unclear (Decision L).** In-scope content with **identifiable
evaluative content whose direction or target can't be resolved**.
- *Identifiable evaluative content* is a favourable or unfavourable
  judgment the annotator can point to in the text, **whose object is
  available**. That means the object is named in the comment, or is
  identified by the C2 prompt-referent rule. This **general
  available-object requirement** applies to every comment except the
  single exception defined below. Examples:
  - an evaluative word or phrase;
  - a proposal, a removal demand, or an ineffectiveness evaluation (C3,
    C4);
  - a definite non-delivery assertion, future or established (C4,
    V6-R2);
  - a recognisable ironic signal (C5);
  - explicit agreement or disagreement with an **available** statement,
    such as the prompt.
- **Not** identifiable evaluative content on its own:
  - **hedged** uncertainty or doubt about whether something will be
    implemented (C4, delivery uncertainty);
  - agreement or disagreement whose object is unavailable and which names
    no in-scope subject (see `U-CONTEXT`).
- **The only exception — target-less Q14 evaluations (V6-R1).** Q14
  ("Please tell us why") follows a Q13 rating whose object is unverified
  (C7). A Q14 answer that names no target can still carry an identifiable
  evaluative **direction** ("Terrible.", "Great."). Such an answer counts as
  identifiable evaluative content **whose object is the unverified Q13
  object**, and is handled **only** by the C7 interim rule:
  - clear direction → Unclear, `U-TARGET (target)`;
  - direction unclear → Unclear, `U-TARGET (direction)`, with `scope also
    unresolved (C1 step 1)`;
  - always confidence 1, `[NEEDS-REVIEW:BORDERLINE]`, `prompt-dependent
    (C2)` and the note `Q13 object unverified (C7)`;
  - regardless of Decision A;
  - **never** Support, Oppose or `OFF_TOPIC` before Q13 is verified.

  **Limits of the exception** — all four conditions must hold:
  1. The comment answers **Q14**.
  2. It names **no target** of its own. A pronoun or demonstrative with no
     antecedent in the comment ("It's terrible.", "This is great.") doesn't
     name one. A Q14 answer that names a target follows the general rules
     (C7 rule 2).
  3. It carries an identifiable evaluative **direction**. A target-less
     Q14 answer with no evaluation is **not** covered (C7 rule 5).
  4. Q13's object is **still unverified**. The exception lapses on
     verification (C7, post-verification rule).

  The exception **does not extend** to other prompts, to replies to
  unavailable comments, to bare agreement (R3), or to any other
  unavailable object. For all of those, the general available-object
  requirement applies unchanged.
- Exactly one sub-reason is recorded:
  - `U-MIXED` (D5): competing favourable and unfavourable inputs, with no
    dominant direction under the C4 dominance test (branch d).
  - `U-TARGET (target)` (D7): the evaluation's direction is clear, but
    whether its target is in scope can't be resolved, and a plausible
    in-scope reading exists (step 1).
  - `U-TARGET (direction)` (D7): the target is in scope, but the intended
    direction can't be recovered. Examples: unresolvable sarcasm (C5), or
    a removal demand whose purpose is unrecoverable (C4, Decision D).
  - `U-CONDITIONAL` (D3): the evaluation depends on a condition whose
    resolution is unknown.
  - `U-CONTEXT` (R3): **both** of the following must be present in the
    comment's own text:
    1. **An explicit endorsement or evaluation signal** directed at
       unavailable content, such as "I agree with…", "I disagree with…",
       "exactly what X said about…", "that proposal is wrong".
    2. **An identifiable in-scope subject** that the unavailable content is
       about, named in the comment (e.g. "…about publishing ministers'
       calendars").

    `U-CONTEXT` then applies because the direction toward the target
    depends on what the unavailable content said. If the direction is
    clear anyway, use Support or Oppose: "I agree with the previous speaker
    that ministers' calendars should be published" is Support.
  - **Bare agreement or disagreement does not qualify for `U-CONTEXT`.**
    Examples: "+1", "Exactly!", "I agree with the comment above", "Well
    said". These have an unavailable object and name no in-scope subject,
    so they contain no identifiable evaluation of the target and don't
    engage with it. Label them **`TOO_SHORT_NONSUBSTANTIVE`**, which
    guidelines §5 defines as no evaluable content, "too brief or generic to
    support any stance determination". Record the note `bare agreement,
    unavailable object (C1, R3)`.
    - **This is an evidence-based exclusion, not a length-based one
      (V6-R3).** The comment is excluded because **its stance target can't
      be established from the available information**, so there is
      nothing to evaluate a stance toward. Its brevity is not the reason.
      Guidelines §5 already says "Length alone is not disqualifying;
      absence of evaluable content is". So:
      - a *long* bare agreement ("I completely agree with everything the
        person before me said; it's so true and needed saying") is still
        excluded;
      - a *short* comment that names an in-scope subject ("Agree on
        open contracting.") is not excluded. It is evaluated normally:
        `U-CONTEXT` if it endorses unavailable content about that
        subject, or Support or Oppose if its direction is recoverable.
      - The code's name ("TOO_SHORT") is the existing label for the
        no-evaluable-content exclusion. It is not a length test; see the
        reviewer questions at the end.
    - **Why the protocol doesn't justify `U-CONTEXT` here:** protocol §5
      (L274–277) sends unexplained references to "something specific (a
      numbered plan, a named program)" to Unclear or review. Bare
      agreement names nothing specific. D7 and guidelines §4 forbid
      guessing the unseen content.
    - **Agreement with the prompt itself** (an available statement) is
      ordinary evaluation under the C2 prompt-referent rule, not
      `U-CONTEXT`.
  - **If both the target and the direction are unresolved**, record
    `U-TARGET (direction)`. The note adds `scope also unresolved (C1
    step 1)`.

**Ambiguity is not, by itself, Unclear.**
- **No identifiable evaluation → Neutral** (if in scope), however
  ambiguous the wording. If an unstated attitude is suspected (possible
  irony with no ironic signal), label it **Neutral**, confidence 1,
  `[NEEDS-REVIEW:BORDERLINE]` (C9).
- **Identifiable evaluation, one resolvable direction → Support or
  Oppose.**
- **Identifiable evaluation, direction or target unresolvable → Unclear**,
  with one sub-reason.

**Annotator test.** *Is there a plausible in-scope reading? Can I point to
an evaluation? Can its direction and target be resolved?*

**Hypothetical examples.**

| Comment | Outcome | Why |
|---|---|---|
| "Rural highways need far more snow clearing — it's shameful." (answering an open-government prompt) | `OFF_TOPIC` | No part has a plausible in-scope reading (step 2). |
| "Is the open data portal updated weekly or monthly?" | Neutral | In scope; no evaluation. |
| "Publishing ministers' calendars builds trust, but it may put their safety at risk; I can't decide which matters more." | Unclear, `U-MIXED` | A favourable and an unfavourable input with no dominance signal (C4 branch d). |
| "So this is the open government plan." (no other content) | Neutral, confidence 1, `[NEEDS-REVIEW:BORDERLINE]` | Refers to the target; possible irony, but nothing evaluative to point to (Decision L). |
| "The open data portal is excellent. Also, potholes on my street need fixing." | Support, note `partial scope (C1): ignored road repair` | The in-scope part is praise; the out-of-scope part is ignored (F5a). |
| "Thanks, see you all next week!" (no other content) | `TOO_SHORT_NONSUBSTANTIVE` | Doesn't engage with the target (O2). |
| "I agree with what the previous speaker said about publishing ministers' calendars." (the earlier comment isn't available) | Unclear, `U-CONTEXT` | An explicit endorsement signal plus a named in-scope subject; the direction depends on the unseen content (R3). |
| "+1, exactly right." (reply; the earlier comment isn't available) | `TOO_SHORT_NONSUBSTANTIVE`, note `bare agreement, unavailable object (C1, R3)` | Bare agreement: no in-scope subject named, so no identifiable evaluation of the target (R3). |
| "Agreed, completely." (answering the prompt "Open government is important because…") | Support, `prompt-dependent (C2)` | Agreement with an available statement (the prompt) that favours the target; not `U-CONTEXT`. |

**Effect on labels.**
- **OFF_TOPIC:** used only when nothing is plausibly in scope. It is never
  converted into a stance.
- **Neutral:** gains the in-scope no-evaluation comments (Decision L).
- **Unclear:** narrows to identifiable-but-unresolvable evaluations.
- **Support / Oppose:** not changed by C1 alone.

## C2. Stance target, process scope and prompts (Decisions A, M, N)

**Ambiguity found.**
- There is no single policy document (protocol §1, §5).
- Broad prompts (Q8 "Did we miss anything?", Q18 expertise) invite
  out-of-scope answers; Q8 is 22/43 Unclear.
- The v3 audit found three problems:
  - the boundary between "public participation" and "the engagement
    process" was undefined (F5c);
  - the rule that the prompt never decides scope clashed with the way Q14
    is used (F1b);
  - `OFF_TOPIC` was broadened without acknowledgement (X2).

**Proposed operational rule.**

**The stance target has two components:**

| Component | Covers | In scope |
|---|---|---|
| **Initiative** | The Government of Canada Open Government initiative's commitments, plans and practices on transparency, open data, open information / access to information, financial transparency and accountability, **and public participation**. Participation means whether and how public input is sought, considered and allowed to influence government decisions, including responsiveness to consultations. | Always |
| **Engagement process** | The design, logistics and conduct of the specific consultation activities that produced this corpus: questionnaire and question design, event scheduling, venues, accessibility, facilitation, and communication about events. | **Only if Decision A is adopted** |

- **Boundary test:**
  - about whether public input **matters or influences decisions** →
    participation (always in scope);
  - about how a specific survey or event was **designed or run** →
    engagement process (Decision A).
- **Openness-angle test (Decision N):** any subject with an openness,
  transparency, accountability or participation angle is in scope, even if
  the underlying programme's subject is not. Related government policy
  without such an angle is `OFF_TOPIC`. This is broader than the
  guidelines' "at all" wording; see Decision N.
- **Recommendations** are in scope only if their aim is in scope (C3).
- **Q18 expertise statements** about in-scope topics are Neutral.

**Prompt rule (Decision M).**
- **What the prompt may do:** identify the **referent** of an otherwise
  target-less evaluation. "Great job" or "Terrible" answering a question
  refers to what that question asks about.
- **What the prompt may not do:** bring an unrelated **subject** into
  scope. "Lower taxes", in answer to any prompt, stays `OFF_TOPIC`.
- When the prompt identified the referent, the note records
  `prompt-dependent (C2)`.
- **An unverified referent is not a resolved referent (R1).** When the
  prompt points to something whose identity isn't known, it identifies the
  referent only as that unknown object. Its scope stays **unresolved**, and
  no Decision makes it resolved. Q14 → "whatever Q13 rated" is the case in
  this corpus; see C7.

**Hypothetical examples — with Decision A's effect.**

| Comment | If A adopted | If A not adopted | Why |
|---|---|---|---|
| Q8: "Raise the minimum wage." | `OFF_TOPIC` | `OFF_TOPIC` | No openness angle (N). |
| Q8: "Publish the evidence behind minimum-wage decisions." | Support | Support | Openness angle; a specific measure (C3). |
| Q18: "I have taught information-management courses for years." | Neutral | Neutral | In-scope expertise; no evaluation. |
| "Another consultation that will be shelved like the last three." | Oppose | Oppose | **Participation** (whether input is acted on), so in scope either way. Definite future non-delivery ("will be shelved") plus established past non-delivery ("like the last three"); both are failure criticism (C4 branch a, V6-R2). |
| "This online survey was so badly designed that I gave up halfway." | Oppose | `OFF_TOPIC` | Engagement process (questionnaire design). Failure criticism (C4 branch a). |
| "The in-person session was well run and people were genuinely listened to." | Support | Support, note `partial scope (C1): ignored session logistics` | "Well run" is process; "genuinely listened to" is participation, in scope either way. |
| "What time does the Halifax session start, and is it wheelchair accessible?" | Neutral | `OFF_TOPIC` | Event logistics (process); no evaluation. |
| "While I have your attention: the speed limit on my street is far too high." | `OFF_TOPIC` | `OFF_TOPIC` | Saying it *at* a consultation doesn't bring it into scope. |
| "Great event! Also, we need lower property taxes." | Support, note `partial scope (C1): ignored property taxes` | `OFF_TOPIC` | The only in-scope part is process praise (O5). |

**Effect on labels.**
- **OFF_TOPIC:** more of it under N; process comments depend on A.
- **Unclear:** fewer.
- **Support:** some topic-only Support labels become candidates for
  Neutral or `OFF_TOPIC` on review.

## C3. Constructive recommendations vs bare topics, information requests and questions (Decisions Q, C)

**Ambiguity found.**
- 7 of 78 Support notes say support is "implied", sometimes from a bare
  topic name.
- Similar suggestions receive both Support and Neutral.

**Proposed operational rule (Decision Q, except the bare-topic default:
Decision C).**
- A **genuine constructive recommendation** → **Support**. It proposes a
  *specific in-scope measure or change* that would extend, restore, fund,
  speed up, improve, or **replace with something stronger** an openness,
  transparency, accountability or participation measure.
  - A proposal **the commenter themselves dismisses** ("they could do X,
    but it won't matter") is **not** a genuine recommendation (C4).
- A **bare topic** (a noun phrase with no proposed measure) → **Neutral**
  (Decision C).
- An **information request** → **Neutral**.
- A **question** → **Neutral**, unless its content proposes a specific
  measure ("why not do X?").
- **Grammar is not evidence of stance.** Neither question marks nor
  imperative mood (nor their absence) decides the label. Decide from **what
  is proposed or asked for**.

**Boundary examples (hypothetical).**

| Boundary | Comment | Outcome | Deciding evidence |
|---|---|---|---|
| Recommendation vs bare topic | "Post every contract amendment online within 30 days." | Support | A specific measure extending transparency. |
| | "Contract amendments." (answering Q8) | Neutral | Names a topic; proposes nothing (C). |
| Recommendation vs information request | "Publish the dataset behind the annual housing report." | Support | Proposes a new disclosure. |
| | "Where can I find the dataset behind the housing report?" | Neutral | Asks where something is. |
| Imperative but not a recommendation | "Tell me which office handles access requests." | Neutral | An imperative information request. |
| Recommendation vs question | "Why not livestream every committee meeting?" | Support | A rhetorical question proposing a measure. |
| | "Are committee meetings livestreamed?" | Neutral | A factual question. |
| Recommendation outside scope | "Build more public swimming pools." | `OFF_TOPIC` | No openness angle (C2, N). |
| "How to" question | "How could smaller agencies be encouraged to publish data?" | Neutral | Asks for methods; proposes nothing. |

**Effect on labels.**
- **Support:** consistent for genuine recommendations.
- **Neutral:** gains bare topics, information requests and plain questions.
- **OFF_TOPIC:** gains out-of-scope proposals.

## C4. Implicit opposition, the corpus-specific application of D4, removal demands and dominance (Decisions B, D, O, P)

**Ambiguity found.**
- Oppose comments missed by every model express opposition without
  opposition words.
- Existing Oppose labels on "not open enough" comments sit uneasily with a
  literal reading of D4.
- The v3 audit found five problems:
  - undefined removal-demand routing (F2);
  - conflicting dominance signals (F3a);
  - branch examples that didn't fit their branch (F3b);
  - the process missing from the definitions (F5c);
  - a risk to D4's own "I hope they deliver" example (X3).

### Decision B — the corpus-specific application of D4 (REVIEWER-DIRECTED)

> In this corpus the stance target (C2) is the Open Government initiative
> *as delivered*. That includes the engagement process if Decision A is
> adopted. A **failure criticism** of it is labelled **Oppose**, even when
> the commenter values openness as a goal. D4's general rule
> (implementation concerns don't override an endorsed goal) still governs
> **problem statements inside recommendations** and **hope or doubt about
> future delivery**. Option B was considered in v1 and is not retained.

### Inputs to the decision tree (definitions)

**Delivery versus effect (R2) — the D4 test, unchanged.** D4 asks: *if the
implementation concern were fully resolved, would the commenter's position
flip?* v6 uses this test to separate **four** kinds of statement about
delivery and effect. This is the position confirmed in the v6 review
(V6-R2):

| Kind | Example | What it is about | Test: fully implemented, would the concern disappear? | Treatment |
|---|---|---|---|---|
| **Hedged delivery uncertainty** | "I doubt they'll implement this." | *Whether* it will be implemented, expressed as hope, uncertainty or hedged doubt | Yes | **Not an input** (D4 general rule; see "Neither" below) |
| **Definite future non-delivery** | "They won't implement this." | *Whether* it will be implemented, asserted rather than doubted | Yes, but the commenter asserts it won't be implemented | **Failure criticism** → Oppose (branch a, if alone) |
| **Established past/present non-delivery** | "They never implement their promises." | *Whether* it has been or is being delivered, asserted as fact | Yes, but the commenter asserts it hasn't been | **Failure criticism** → Oppose (branch a, if alone) |
| **Ineffectiveness despite implementation** | "Even if implemented, it won't work." | Whether it *would work* | No | **Unfavourable input** (ineffectiveness evaluation) → Oppose (branch a, if alone) |

**Rationale (V6-R2).** A definite assertion that an in-scope initiative or
commitment *will not* be implemented is a negative assessment of its
expected delivery and its credibility. It need not describe a failure that
has already happened, so it is failure criticism in its own right; it
doesn't have to be grounded in past failure. Hedged doubt asserts nothing,
so it stays delivery uncertainty and is never automatically Oppose
(Decision B).

**Telling hedged from definite (delivery statements only).**
- **Hedged:** a doubt or uncertainty marker governs the delivery claim.
  Examples: "I doubt…", "I'm not sure…", "I don't think they'll…",
  "probably won't", "might not", "we'll see whether…", "I hope…".
- **Definite:** the non-delivery is asserted without such a marker.
  Examples: "they won't…", "they'll never…", "no way they'll…", "it will
  be shelved".
- If it can't be told whether a marker governs the claim (e.g. a
  rhetorical "They're not going to do it, are they?"), treat it as
  **hedged**, which is the conservative reading. Label it confidence 1,
  `[NEEDS-REVIEW:BORDERLINE]`.
- The hedged/definite distinction applies **only to delivery**
  statements. An ineffectiveness evaluation is unfavourable whether or not
  it is hedged, because the concern survives full implementation. So "I
  don't think they'll do it" is hedged delivery uncertainty, but "I don't
  think it will change anything" is an ineffectiveness evaluation.

**"Nothing will come of this"** is read by its object:
- non-delivery ("it will never happen") → definite future non-delivery;
- no effect ("it will change nothing") → ineffectiveness.

If the object can't be told apart, both readings are unfavourable, so
branch a or the dominance test applies either way.

**Precedence of D4's problem-statement test.** The four-way split
classifies delivery statements that **stand on their own**. A delivery
statement that only describes the specific problem a proposed fix
addresses is a **problem statement** under D4's test (see "Neither"
below), whatever its tense or certainty. Apply the problem-statement test
first.
- "They never publish contract data on time; set a legal 30-day
  deadline." → problem statement → Support (branch b).
- "They never implement their promises. If they want trust, set a legal
  deadline." → the first sentence stands as a verdict on the government's
  delivery generally → failure criticism + recommendation → dominance test.

**Unfavourable inputs:**
- **Failure criticism.** A *standalone* negative verdict on the
  initiative, on government openness generally, on a whole in-scope measure
  or system, or (under A) on the engagement process. The verdict says it is
  absent, inadequate, failing, untrustworthy or pointless. It includes
  **definite future non-delivery** and **established past/present
  non-delivery** (table above, V6-R2).
- **Ineffectiveness evaluation** (called "dismissal" in v4). The belief
  that it would not work **even if implemented** (table above).
- **Removal demand.** A call to stop, abolish, repeal, shut down or
  withdraw an in-scope openness measure, **without** stating an aim to
  replace it with something stronger.

**Favourable inputs:**
- **Constructive recommendation (C3).** This includes a
  **replacement/strengthening proposal**: a call to remove or replace a
  measure that states the stronger or better openness measure or aim
  ("repeal it and replace it with one that has real penalties").
- **Explicit praise** of the target.

**Neither — the D4 general rule (X3):**
- **A problem statement inside a recommendation.** This describes a
  specific shortcoming offered as the reason for the proposed fix ("search
  is slow, so add filters"). It is part of the recommendation, not failure
  criticism.
  - *Test:* remove the proposal. If what's left still stands as a verdict
    on the initiative or a whole measure ("it's useless", "there is no
    transparency"), it is failure criticism. If it only describes the
    problem the proposal fixes, it is a problem statement.
- **Hedged delivery uncertainty** (hope, uncertainty or hedged doubt about
  *whether* it will be implemented), without asserting present or past
  failure and without a definite assertion of future non-delivery
  (V6-R2).
  - Combined with an endorsed goal → **Support** ("Great plan — I just
    hope they follow through"; "Good idea, though I doubt they'll do
    it").
  - Alone, with no endorsement → no identifiable evaluation → **Neutral**,
    confidence 1, `[NEEDS-REVIEW:BORDERLINE]` ("We'll see whether they
    deliver on these open-data commitments").
  - Combined with an ineffectiveness evaluation → that evaluation is an
    unfavourable input, and the uncertainty adds nothing.
  - It never becomes Oppose automatically (Decision B).

### Decision tree (Decision O, REVIEWER-DIRECTED)

Apply the first branch that matches. Only in-scope inputs count (C1 partial
scope).

| Branch | The comment contains | Label |
|---|---|---|
| **a** | Unfavourable inputs only | **Oppose** |
| **b** | Favourable inputs only | **Support** |
| **c** | Both, and the dominance test identifies one direction | **That direction** |
| **d** | Both, and the dominance test identifies no single direction | **Unclear, `U-MIXED`** |

v3 defined a–d for failure criticism versus constructive improvement.
Applying the same tree to ineffectiveness evaluations, removal demands and
praise, so every mixed case uses one logic, is Decision P (RECOMMENDED).

### Dominance test (Decision P, RECOMMENDED)

**Signals** — only the **commenter's own framing** counts:
- **S1 — explicit overall verdict.** The commenter states their net
  position ("overall…", "on balance…", "all in all…"). An evaluation of one
  part is not a verdict.
- **S2 — minimising framing.** The commenter marks one side as minor or
  secondary ("a minor gripe", "a side issue", "that aside"). The other side
  dominates. This is D3's minor-caveat principle, applied as D4 refers to
  it (O1).
- **S3 — discounting.** The commenter explicitly discounts one side ("…but
  it won't make any difference", "…not that it matters"). The other side
  dominates. When the discount is itself an ineffectiveness evaluation of
  the favourable side ("…but even if they do it, it won't change
  anything"), it is **both** the unfavourable input that makes the comment
  a "both" case **and** the S3 signal. It is counted once, not as two
  inputs.

**Precedence:**
1. An **S1** verdict decides, overriding S2 and S3.
2. Two **conflicting S1** verdicts (self-contradiction, D5) → branch d.
3. With no S1: if every S2/S3 signal points the same way → that direction.
   If they point different ways → **branch d**.
4. **No signal** → branch d. An explicit refusal to weigh ("I can't say
   which matters more") is not a signal; it confirms branch d.
5. **Intensity of wording is never a signal** (D1).

### Removal demands (Decision D, RECOMMENDED — rewritten, F2)

1. **A removal demand only** (with or without failure criticism) → branch
   a → **Oppose**.
2. **A replacement/strengthening proposal** → a favourable input (C3) →
   branch b (**Support**), or branch c/d if unfavourable inputs are also
   present.
3. **A removal demand plus favourable inputs** → the dominance test,
   branch c or d. Never automatically `U-TARGET`.
4. **`U-TARGET (direction)`** only when the comment makes the removal's
   purpose genuinely unrecoverable, so it can't be told whether the
   commenter opposes openness or wants the measure gone *for* openness.

### Hypothetical examples (each checked against its branch)

| Branch | Comment | Inputs found | Outcome |
|---|---|---|---|
| a | "There's no real transparency in Ottawa." | Failure criticism | Oppose |
| a | "Another consultation that will be shelved like the last three." | Definite future non-delivery ("will be shelved") plus established past non-delivery ("like the last three"); both are failure criticism (V6-R2; participation, in scope regardless of A) | Oppose |
| a | "They never follow through on these promises." | Established past/present non-delivery, which is failure criticism (V6-R2) | Oppose |
| a | "They won't implement the open-contracting plan." | Definite future non-delivery, which is failure criticism in its own right; no past failure needed (V6-R2) | Oppose |
| a | "Even if the open-contracting plan is implemented, it won't work." | Ineffectiveness despite implementation (V6-R2) | Oppose |
| a | "Even if they publish every contract, no one in Ottawa will be held to account." | Ineffectiveness evaluation: the concern survives full implementation (R2) | Oppose |
| a | "This initiative is a sham. They could post the budgets, I suppose, but it won't change anything." | Failure criticism + ineffectiveness evaluation. The budget idea is dismissed by the commenter, so it is **not** a recommendation. | Oppose |
| a | "Shut down the open data portal; it's money down the drain." | Removal demand + failure criticism | Oppose |
| b | "Make the portal's search return results by date." | Recommendation | Support |
| b | "Search on the portal is slow; add an index so results load faster." | Recommendation with a problem statement (the slowness is the reason for the fix; not a verdict) | Support |
| b | "Repeal the transparency act and replace it with one that has real penalties." | Replacement/strengthening proposal | Support |
| b | "Great plan — I just hope they actually follow through." | Praise; the hope is delivery uncertainty, not an input (D4) | Support |
| b | "Good idea, though I doubt they'll do it." | Praise; hedged doubt about *whether* it will be done is delivery uncertainty, not an input (D4, V6-R2) | Support |
| b | "They never publish contract data on time; set a legal 30-day deadline." | The problem-statement test is applied first: "never publish on time" only describes the problem the deadline fixes, so it is a problem statement, not failure criticism (D4) | Support |
| c → Oppose (S1) | "The portal's map view is handy, but overall this initiative is a failure." | Praise + failure criticism; S1 verdict | Oppose |
| c → Support (S2) | "The access-to-information system is broken, but that's a side issue for me — the open data portal has been invaluable and should be extended to provincial data." | Failure criticism (framed as minor) + praise + recommendation; S2 | Support |
| c → Oppose (S3) | "The new request form is nice, but it won't make any difference while the whole system stays broken." | Praise discounted by an ineffectiveness evaluation (S3) + failure criticism | Oppose |
| c → Oppose (S3) | "Good idea in theory, but even if they do it, it won't change anything." | Praise + an ineffectiveness evaluation that discounts it (one input, also S3). Contrast with "Good idea, though I doubt they'll do it", which is branch b (R2). | Oppose |
| c → Oppose (S1 beats S2) | "Overall the initiative is failing — even though the open data portal, the only part that really matters to me, is excellent." | S1 says Oppose; S2 would favour Support; S1 takes precedence | Oppose |
| d (no signal) | "Access requests take months and the system is failing, yet the new online request form is a real improvement that should be extended to every department — I can't say whether things are better or worse overall." | Failure criticism + praise + recommendation; no signal | Unclear, `U-MIXED` |
| d (removal + favourable) | "Shut down the open data portal — though the new contracts database is excellent and should be expanded." | Removal demand + praise + recommendation; no signal | Unclear, `U-MIXED` |
| d (conflicting S2/S3) | "The access system is broken, but that's a side issue; the new online form is a real step forward — not that it will make any difference." | Failure criticism minimised by S2 (favours Support) + praise discounted by S3 (favours Oppose); no S1 | Unclear, `U-MIXED` |
| d (past non-delivery + recommendation) | "They never implement their promises. If they want trust, set a legal deadline." | "They never implement their promises" still stands as a general verdict once the proposal is removed: established non-delivery (failure criticism) + recommendation; no signal | Unclear, `U-MIXED` |
| `U-TARGET (direction)` | "Repeal the access law. Everyone knows what it's really for." | A removal demand whose purpose is unrecoverable | Unclear, `U-TARGET (direction)`, confidence 1, `[NEEDS-REVIEW:BORDERLINE]` |
| Neutral (delivery uncertainty) | "We'll see whether they deliver on these open-data commitments." | Delivery uncertainty only; refers to the target; no endorsement, no failure asserted | Neutral, confidence 1, `[NEEDS-REVIEW:BORDERLINE]` |
| Neutral (delivery uncertainty) | "I'm not sure they'll actually implement the open-contracting plan." | Hedged doubt about *whether* it will be implemented; no endorsement, no ineffectiveness evaluation | Neutral, confidence 1, `[NEEDS-REVIEW:BORDERLINE]` |
| Neutral (delivery uncertainty) | "I doubt they'll implement the open-contracting plan." | Hedged delivery uncertainty, alone. Contrast with "They won't implement the open-contracting plan." → Oppose (V6-R2). | Neutral, confidence 1, `[NEEDS-REVIEW:BORDERLINE]` |
| Neutral (hedged/definite unclear) | "They're not going to implement the open-contracting plan, are they?" | A rhetorical form; can't tell whether a doubt marker governs the claim → treated as hedged, the conservative reading (V6-R2) | Neutral, confidence 1, `[NEEDS-REVIEW:BORDERLINE]` |

**Effect on labels.**
- **Oppose:** gains implicit cases. v1 performance-criticism Oppose labels
  stay consistent with branch a.
- **Support:** keeps recommendations, including those with problem
  statements.
- **Unclear (`U-MIXED`):** used only under branch d.
- **Known consequence:** comments that combine a whole-measure verdict with
  a fix ("X is useless; do Y") go to branch d unless the commenter signals
  dominance. See T1 monitoring and the unresolved points below.

## C5. Sarcasm (Decision R)

**Ambiguity found.** D7 covers sarcasm with an ambiguous target, but not
how to label sarcasm that can be resolved.

**Proposed operational rule.**
- **Resolvable sarcasm** → its intended direction (D1, D7). The target has
  a plausible in-scope reading and the literal praise is clearly ironic.
  Typical signs: exaggerated praise paired with a negative fact, scare
  quotes around the policy's own terms. Confidence follows §6.2.
- **Unresolvable sarcasm** → Unclear, confidence 1,
  `[NEEDS-REVIEW:BORDERLINE]`. It needs identifiable evaluative content (an
  evaluative word or ironic signal) plus one of:
  - the direction can't be recovered (sincere or ironic?) →
    `U-TARGET (direction)`;
  - the direction is clear, but whether the target is in scope can't be
    resolved, with a plausible in-scope reading present →
    `U-TARGET (target)` (C1 step 1).
- **No plausible in-scope reading at all** → `OFF_TOPIC` (C1 step 2),
  sarcastic or not.
- **Suspected irony with no identifiable evaluation or ironic signal** →
  Neutral, confidence 1, `[NEEDS-REVIEW:BORDERLINE]` (C1).

**Why confidence 1 (conceptual).** Protocol §6.2 defines confidence 1 as "a
genuine borderline case between two labels". Unresolvable sarcasm is
exactly that: an intended direction exists but can't be recovered.
Confidence describes closeness to a label boundary, not the annotator's
certainty that the item is ambiguous. The `[NEEDS-REVIEW:BORDERLINE]` marker
is the C9 interim convention layered on top; it is not the reason for
confidence 1.

**Hypothetical examples.**

| Comment | Outcome | Why |
|---|---|---|
| "Oh wonderful, another 'open' portal where every page says 'redacted'." | Oppose (confidence by §6.2) | Ironic praise plus a negative fact; target in scope; resolvable. |
| "Great job, everyone. Truly inspiring work." (Q14, no other content) | Unclear, `U-TARGET (direction)`, confidence 1, `[NEEDS-REVIEW:BORDERLINE]`, `prompt-dependent (C2)` | The referent is Q13's unverified object, so the scope is unresolved whether or not A is adopted (C7 interim rule, R1). Sincere or ironic can't be told either. The note adds `scope also unresolved (C1 step 1); Q13 object unverified (C7)`. |
| "Brilliant work as always, Ottawa." (Q8, no other content) | Unclear, `U-TARGET (target)`, confidence 1, `[NEEDS-REVIEW:BORDERLINE]` | Ironic signal ("as always"), so the direction is unfavourable. But "Ottawa" may be government in general or the initiative; a plausible in-scope reading exists (C1 step 1). |
| "So this is the open government plan." (no other content) | Neutral, confidence 1, `[NEEDS-REVIEW:BORDERLINE]` | Refers to the target; nothing evaluative to point to. |
| "Heard the same pledge at last year's town hall." | Oppose (C4 branch a) | Implies the earlier pledge wasn't delivered: established past non-delivery, which is failure criticism (V6-R2). Not sarcasm. |

**Effect on labels.**
- **Oppose:** gains resolvable sarcasm.
- **Unclear:** keeps only unresolvable sarcasm with identifiable
  evaluation.
- **Neutral:** keeps suspected-but-unsignalled irony.
- **OFF_TOPIC:** takes sarcasm with no in-scope reading.

## C6. Negation that is not a stance signal (Decision S)

**Ambiguity found.** Negation occurs in every class. In training, the
comments containing a negation or contrast word are: Support 15, Oppose 9,
Neutral 10, Unclear 20.

**Proposed operational rule.**
- Negation is a stance cue only when it negates an evaluation of, or a
  commitment to, the target.
- Negation inside these is **not** a stance cue:
  - a description of oneself, others or circumstances;
  - a clarification of scope;
  - a definition;
  - a factual statement.

  Label such comments from the rest of their content.
- The note records `non-stance negation (C6)` when this decided the label.

**Hypothetical examples.**

| Comment | Outcome |
|---|---|
| "Offer the reports in large print for people who can't read small screens." | Support (C3). The "can't" describes readers. |
| "I haven't visited the open data site yet." | Neutral |
| "I don't think publishing these figures will change anything." | Oppose (C4 branch a: a hedged ineffectiveness evaluation. The concern survives publication, so the hedge doesn't matter; V6-R2) |
| "I don't think they'll publish these figures." | Neutral, confidence 1, `[NEEDS-REVIEW:BORDERLINE]`. The negation sits inside a doubt marker, so it is hedged delivery uncertainty, not a stance cue (V6-R2). |
| "They won't publish these figures." | Oppose (C4 branch a). The negation asserts definite future non-delivery of an in-scope commitment, so it is a stance cue (V6-R2). |

## C7. Q14 and the missing satisfaction rating (Decisions U, E)

**Ambiguity found.**
- Q14 ("Please tell us why") follows a Q13 satisfaction rating that isn't
  in the annotation file.
- Q14 is the most Oppose-rich prompt (11 of 42 train + val comments).
- **What Q13 rated is unverified (F5b).** It may be the initiative's
  openness, the consultation or questionnaire itself, or something else.

**Information available — kept separate:**

| | Annotator | Eventual model (Experiments 1–3 design) |
|---|---|---|
| Comment text | Yes | Yes (`normalized_text`) |
| Prompt text (`policy_section`), including that Q14 follows a rating | Yes | **No** |
| Q13 rating value | **No** | **No** |
| What Q13 rated | **Not verified** | — |

**Proposed operational rule.**
1. **Never infer, assume or record a guessed rating**, and never treat
   prompt-level base rates as evidence.
2. A Q14 answer that **names its own target** is labelled from its text
   under C1–C4. The prompt isn't needed.
3. **Target-less Q14 evaluations — conservative interim rule (R1; made an
   explicit C1 exception in V6-R1).** This covers answers like "Terrible."
   or "Great job." that name no target but carry an identifiable
   evaluative direction. It applies **until Q13's object is verified**.
   It is the **only** exception to C1's available-object requirement, and
   its four limits are set out in C1 step 5.
   - **Referent.** The prompt identifies the referent only as "whatever
     Q13 rated". That object is unverified, so **its scope is unresolved
     whether or not Decision A is adopted**. Decision A puts the engagement
     process in scope, but Q13 may have rated something else (such as
     government services in general) that no decision puts in scope.
     **Decision A is therefore never used to resolve a Q14 referent.**
   - **Scope.** The answers come from the Open Government "Get Involved"
     questionnaire, so a plausible in-scope reading exists. They are
     therefore **never `OFF_TOPIC`** under this rule (C1 step 1).
   - **Label:**
     - direction resolvable → **Unclear, `U-TARGET (target)`**;
     - direction unresolvable → **Unclear, `U-TARGET (direction)`**, with
       `scope also unresolved (C1 step 1)` in the note;
     - no identifiable evaluation → rule 5.

     Never Support or Oppose. Every evaluative case gets confidence 1 and
     `[NEEDS-REVIEW:BORDERLINE]`.
   - **Tags:** `prompt-dependent (C2)`, plus the note `Q13 object
     unverified (C7)`.
   - **Why this is conservative:**
     - It assigns no stance that depends on an unknown object.
     - It doesn't inflate Oppose from the most Oppose-rich prompt.
     - It doesn't exclude evaluations that may well be in scope.
     - Every affected item is tagged, so all of them can be re-reviewed
       once the object is known.
   - **After verification (inactive until then).** If Q13's object is
     verified, which is Decision E (OPTIONAL / DEFERRED), the tagged items
     are re-reviewed through the adjudication log (C10):
     - Q13 rated the initiative or government openness → label by
       direction (C4/C5);
     - it rated the consultation or questionnaire → in scope only under
       Decision A, otherwise `OFF_TOPIC`;
     - it rated something outside the target → `OFF_TOPIC`.

     This rule doesn't change Decision E's status. It only records what
     verification would allow.
4. A Q14 answer about an **unrelated subject** is `OFF_TOPIC`. The prompt
   can't bring it into scope.
5. Q14 answers with **no identifiable evaluation** follow C1 steps 4–5 and
   are **not** covered by the target-less exception (V6-R1):
   - Neutral if they engage with an in-scope subject (e.g. "I haven't
     really needed government information");
   - otherwise the appropriate exclusion code.

   This makes v5's wording ("are Neutral") consistent with C1 step 4. See
   the reviewer questions.

**Documented limitations.**
- Labels tagged `prompt-dependent (C2)` can't be reproduced by a text-only
  model. Counting them shows how much of Q14 is unlearnable without the
  prompt.
- Whether to give future models the prompt as a feature is a separate
  modelling decision.
- **Until Q13 is verified, target-less Q14 evaluations are systematically
  Unclear (`U-TARGET`), under either Decision A outcome.** This lowers the
  Oppose yield from Q14 relative to v4. That is deliberate: those Oppose
  labels would rest on an unknown object.
- **Recovering the rating is Decision E (OPTIONAL / DEFERRED).** If it is
  ever done, through a verified, read-only join, the rating would be stored
  as metadata, hidden during annotation, used only for post-hoc analysis,
  and never a label source. Rules 1–5 apply either way.

**Hypothetical examples (Q14).**

| Comment | If A adopted | If A not adopted | Why |
|---|---|---|---|
| "Because I can never find anything on the federal websites." | Oppose | Oppose | Names its target (access to government information); failure criticism (C4 branch a). |
| "Terrible." | Unclear, `U-TARGET (target)`, confidence 1, `[NEEDS-REVIEW:BORDERLINE]`, `prompt-dependent (C2)` | The same | Target-less, with a resolvable unfavourable direction. The referent is Q13's unverified object, so the scope is unresolved and A doesn't resolve it (rule 3, R1). |
| "Great, really pleased." | Unclear, `U-TARGET (target)`, confidence 1, `[NEEDS-REVIEW:BORDERLINE]`, `prompt-dependent (C2)` | The same | As above, with a resolvable favourable direction. Not Support until Q13 is verified (R1). |
| "The questions were confusing and far too long." | Oppose | `OFF_TOPIC` | Names the questionnaire, which is process (C2). |
| "I haven't really needed government information." | Neutral | Neutral | No identifiable evaluation. |
| "The new open data site is excellent, but the access-to-information office is a shambles, and overall I honestly can't say whether things have improved." | Unclear, `U-MIXED` | Unclear, `U-MIXED` | Praise + failure criticism; no dominance signal (C4 branch d). |
| "Lower taxes would make me happier." | `OFF_TOPIC` | `OFF_TOPIC` | Unrelated subject; the prompt can't bring it into scope. |

## C8. Annotation-note quality and template (Decision H)

**Ambiguity found.**
- One Unclear note is the placeholder ".".
- No note cites a rule code.
- The same wording is attached to different labels.

**Proposed operational rule — note template.**

```
[optional C9 marker] <Label or exclusion code> — <rule code(s) and tags> — evidence: <part of the comment that decided it> — reasoning: <why that evidence gives this label>
```

- **Fields:** separated by a spaced em dash ( — ), in this order. A C9
  marker, when required, comes first.
- **Rule codes:** D1–D8, C1–C10, and C4 branch letters.
- **Tags:** for Unclear, the sub-reason comes first (e.g.
  `U-TARGET (direction)`). Also record, when they apply:
  - `prompt-dependent (C2)`;
  - `partial scope (C1): ignored <topic>`;
  - `non-stance negation (C6)`.
- **Required for:** Unclear, Oppose, Support via C3, sarcasm (C5),
  `OFF_TOPIC`, and every confidence-1 label. Recommended for all others.
- **Not acceptable:** placeholders (".", "n/a", "unclear", "see comment"),
  and "no position expressed" on any label other than Neutral.
- `annotation_notes` is free text, so **no schema change** is needed. A
  validator warning for the template is future work, not implemented.

**Hypothetical example notes.**

```
Unclear — U-MIXED (C1, C4 branch d, D5) — evidence: praises publishing calendars; objects to the safety risk — reasoning: favourable and unfavourable inputs, no dominance signal.
OFF_TOPIC — C1 step 2, C2, N — evidence: asks for more snow clearing — reasoning: no part has a plausible in-scope reading.
Support — C3, C4 branch b — evidence: proposes posting contract amendments within 30 days — reasoning: specific measure extending transparency.
Oppose — C4 branch a, B — evidence: states there is no real transparency — reasoning: standalone failure criticism of the initiative as delivered.
Support — C4 branch c (S2), C1 — evidence: calls the ATI system broken but "a side issue"; praises and asks to extend the portal — reasoning: commenter minimises the unfavourable side.
Support — C1, partial scope (C1): ignored road repair — evidence: praises the open data portal — reasoning: only the in-scope part is evaluated.
[NEEDS-REVIEW:BORDERLINE] Unclear — U-TARGET (direction) (C1, C5, C7, D7), prompt-dependent (C2) — evidence: "great job", "truly inspiring" answering Q14 — reasoning: sincere vs ironic cannot be determined; scope also unresolved (C1 step 1); Q13 object unverified (C7).
[NEEDS-REVIEW:BORDERLINE] Unclear — U-TARGET (target) (C1, C7), prompt-dependent (C2) — evidence: "terrible" answering Q14, no other content — reasoning: unfavourable direction is clear, but the referent is Q13's unverified object; Decision A not used to resolve it (R1).
Oppose — C4 branch a, V6-R2 — evidence: says that even if every contract were published no one would be held to account — reasoning: ineffectiveness despite implementation; concern survives full implementation.
Oppose — C4 branch a, B, V6-R2 — evidence: "they won't implement the open-contracting plan" — reasoning: definite future non-delivery of an in-scope commitment; failure criticism without needing past failure.
Oppose — C4 branch a, B, V6-R2 — evidence: "they never implement their promises" — reasoning: established past/present non-delivery; failure criticism.
Support — C4 branch b, B, V6-R2 — evidence: calls it a good idea; doubts they will do it — reasoning: praise plus hedged delivery uncertainty, which is not an input.
[NEEDS-REVIEW:BORDERLINE] Neutral — C1, C4, V6-R2 — evidence: "I doubt they'll implement the open-contracting plan" — reasoning: hedged delivery uncertainty alone; no endorsement, no ineffectiveness evaluation.
Unclear — U-CONTEXT (C1, R3) — evidence: "agree with the previous speaker" about publishing ministers' calendars; earlier comment unavailable — reasoning: endorsement signal and named in-scope subject, but direction depends on unseen content.
TOO_SHORT_NONSUBSTANTIVE — C1, R3, V6-R3 — evidence: "+1, exactly right" replying to an unavailable comment — reasoning: bare agreement, unavailable object, no in-scope subject named; the stance target cannot be established (evidence-based, not length-based).
[NEEDS-REVIEW:BORDERLINE] Neutral — C1, C5, L — evidence: remark naming the plan, no evaluative word or ironic signal — reasoning: possible irony suspected; nothing identifiable.
[NEEDS-REVIEW:REQUESTED conceptual=3] Support — C3, C4 branch b — evidence: proposes publishing all grant decisions online — reasoning: label is clear; review requested as a calibration check on the first comment from a new prompt type.
```

## C9. Needs-review convention (Decision J)

**Ambiguity found.**
- No needs-review field exists. A batch row has exactly the 12 columns in
  `scripts/annotation/schema.py` `REQUIRED_COLUMNS`.
- v3 used one marker for two different things, so a label's real
  confidence could be lost (F4).

**Two concepts:**

| | Conceptual confidence | Needs review |
|---|---|---|
| What it is | A property of the label: how close it sits to a label boundary (§6.2: 1 Low, 2 Medium, 3 High). | A workflow request: send this item to adjudication-style review (guidelines §3 step 10). |
| Defined by | Protocol §6.2. **The concept is unchanged by this proposal.** | This proposal (C9), **temporary** |

**Interim convention — existing fields only, no schema change.**
- **Marker syntax.** Exactly one of the following, at the **very start** of
  `annotation_notes`, followed by a space and the C8 template:
  - `[NEEDS-REVIEW:BORDERLINE]` — the label is a genuine §6.2 borderline
    case. Its conceptual confidence is 1.
  - `[NEEDS-REVIEW:REQUESTED conceptual=2]` or
    `[NEEDS-REVIEW:REQUESTED conceptual=3]` — the label is conceptually
    Medium or High, but the annotator requests review. The reasoning field
    says why.
- **Stored value.** Every marked item stores `annotation_confidence = 1`.
  For BORDERLINE, stored = conceptual. For REQUESTED, the stored value
  **deliberately differs** from the conceptual value, which is kept in the
  marker. The concept of confidence is unchanged, but the stored field
  carries a convention for REQUESTED items. Analyses must read conceptual
  confidence from the marker, not from the field.
- **Valid and invalid combinations:**

| `annotation_confidence` | Note starts with | Valid? |
|---|---|---|
| 1 | `[NEEDS-REVIEW:BORDERLINE]` | Valid |
| 1 | `[NEEDS-REVIEW:REQUESTED conceptual=2]` or `…=3]` | Valid |
| 1 | no marker | **Invalid** (v2 and later) |
| 1 | `[NEEDS-REVIEW:REQUESTED conceptual=1]` | **Invalid** — use BORDERLINE |
| 2 or 3 | any marker | **Invalid** |
| any | a marker not at the start, more than one marker, or other syntax | **Invalid** |

- **Handling invalid states.** They are corrected through the v2 re-review
  and adjudication log (C10). Automatic detection is a future validator
  warning, not implemented. **No schema field is introduced.**
- **v1 files.** The 3 v1 confidence-1 labels have no marker. The convention
  applies to v2 and later only, so they are not invalid retroactively.
- **Interpretation.** Counts of `annotation_confidence = 1` in v2 or later
  mean "borderline or review-requested". Split them by marker for any
  analysis of conceptual confidence (O6: the marker alone now identifies
  the case).

## C10. v1 immutability and logged v2 re-review (Decision G, REVIEWER-DIRECTED)

- `annotation_batch_001.csv`, its `original_backup.csv` and
  `stance_annotations_final.csv` are **v1 and immutable**. They are never
  edited, overwritten or regenerated.
- Applying C1–C9 to the 250 comments is a **v2 re-review**. It is recorded
  in a **separate v2 label file**, plus an **adjudication log** entry per
  change (guidelines §7): comment ID, v1 label, v2 label, rule codes and
  tags, justification, date. Unchanged items are recorded as confirmed.
- v1 and v2 coexist. Experiments 1–3 and the current splits stay tied to
  v1.
- The re-review happens **after the repeat pass** (Decision F). It never
  touches `repeat_annotation_plan.json`, `annotation_state.json` or the
  repeat-pass files.
- The file names and formats for the v2 label file and adjudication log are
  future work needing their own approval.

---

## T1. Monitoring note — taxonomy (Decisions K, V; not implemented)

The taxonomy is preserved (K). T1 proposes no change.

- **Unclear count.** About **6–8 of 66** train + val v1 Unclear labels match
  a v5 Unclear sub-reason:
  - ≈6 with an unresolved direction or target;
  - 2 v1 `U-CONTEXT` candidates, which qualify under v5 **only if** they
    name an in-scope subject (R3). Otherwise they become
    `TOO_SHORT_NONSUBSTANTIVE`. This can only be settled in the v2
    re-review.

  One more has a placeholder note and can't be assessed (O3).
- **Recommended (Decision V):** report the actual post-re-review Unclear
  count **by sub-reason**, as a data-sufficiency figure, including:
  - how many `U-MIXED` items come from C4 branch d;
  - how many `U-TARGET` items come from the Q14 interim rule (R1);
  - how many bare-agreement items moved to `TOO_SHORT_NONSUBSTANTIVE`
    (R3). Any taxonomy question needs a
  separate, explicit request.

---

## Decisions register

| # | Decision | Position | Status |
|---|---|---|---|
| A | Stance target includes the **engagement process** (C2). | Adopt; process in scope. Participation is in scope regardless. | RECOMMENDED |
| B | The corpus-specific application of D4 (Option A); hope or doubt about future delivery is never automatically Oppose (C4). | Failure criticism is Oppose. The detailed handling of problem statements and doubt is Decision P. | REVIEWER-DIRECTED |
| C | Bare topic names answering suggestion prompts (C3). | Neutral. | RECOMMENDED |
| D | Removal demands and replacement/strengthening proposals (C4). | As rewritten in C4: through the a–d tree; `U-TARGET` only when the purpose is unrecoverable. | RECOMMENDED |
| E | Recovery of Q13 ratings (C7). | Not needed; if done, hidden and analysis-only. | OPTIONAL / DEFERRED |
| F | Adopt the clarifications after the 38-item repeat pass under the original protocol. | After. | REVIEWER-DIRECTED |
| G | v1 immutable; logged v2 re-review (C10). | Adopt. | REVIEWER-DIRECTED |
| H | C1 sub-reason tags, including the `U-CONTEXT` minimum signal and bare agreement → `TOO_SHORT_NONSUBSTANTIVE` as an evidence-based, not length-based, exclusion (R3, V6-R3); C-codes, tags and the C8 note template. | Adopt; validator warning is future work. | RECOMMENDED |
| I | Record the protocol version per future batch. | Through a separate future format task; no schema change here. | RECOMMENDED |
| J | Interim needs-review convention with BORDERLINE / REQUESTED markers (C9). | Adopt as temporary; no schema field. | RECOMMENDED |
| K | The four-class taxonomy and four exclusion codes; T1 monitoring-only. | Preserve. | REVIEWER-DIRECTED |
| L | **Redefine the Unclear/Neutral boundary** (C1 steps 4–5; ambiguity rule). Requires amending the authoritative texts listed above. | Adopt. | REVIEWER-DIRECTED |
| M | Scope tests: OFF_TOPIC only with no plausible in-scope reading; uncertain target → proceed as in scope; partial scope; the prompt-referent rule, where an unverified referent stays unresolved and Decision A doesn't resolve it (R1) (C1 steps 1–2, C2). | Adopt. | REVIEWER-DIRECTED |
| N | **Redefine the OFF_TOPIC boundary** with the openness-angle test, broader than the guidelines' "at all" (C2). Requires amending guidelines §5. | Adopt. | RECOMMENDED |
| O | The C4 a–d decision tree, and branch d when signals can't establish a dominant direction. | Adopt. | REVIEWER-DIRECTED |
| P | C4 input definitions: failure criticism (including definite future and established past/present non-delivery), ineffectiveness evaluation, recommendation, praise; the four-way delivery-versus-effect split by D4's own test (R2, V6-R2), with the hedged-versus-definite markers; the problem-statement test, applied before the split; hedged delivery uncertainty alone → Neutral at confidence 1. Also the dominance signals and precedence (S1 > S2/S3; conflict → d), and applying a–d to all favourable and unfavourable inputs. | Adopt. | RECOMMENDED |
| Q | C3 boundaries between recommendations, bare topics, information requests and questions; the grammar-is-not-evidence rule. | Adopt. | REVIEWER-DIRECTED |
| R | C5 sarcasm rules (resolvable / unresolvable / suspected). | Adopt. | RECOMMENDED |
| S | C6 non-stance negation rule. | Adopt. | RECOMMENDED |
| U | C7 Q14 rules: no rating inference; target-named answers labelled from text; the **conservative interim rule** for target-less answers until Q13 is verified, where they are Unclear `U-TARGET` under either A outcome (R1). That rule is the only, explicitly limited exception to C1's available-object requirement (V6-R1). Also: post-verification handling (inactive); limitations. | Adopt. | RECOMMENDED |
| V | T1 monitoring report of post-re-review Unclear counts by sub-reason. | Adopt. | RECOMMENDED |

(No decision T, to avoid confusion with the T1 monitoring note.)

**APPROVED: none.**
- **RECOMMENDED:** A, C, D, H, I, J, N, P, R, S, U, V.
- **REVIEWER-DIRECTED:** B, F, G, K, L, M, O, Q.
- **OPTIONAL / DEFERRED:** E.

Nothing becomes APPROVED except by formal adoption.

**Reviewer-confirmed positions in the v6 review — recorded, not
re-statused.** The reviewer confirmed three positions:

| Position | Lives in | Status of that decision |
|---|---|---|
| V6-R1 — the target-less Q14 exception and its interim rule | U (and M) | RECOMMENDED (M: REVIEWER-DIRECTED) |
| V6-R2 — the four-way delivery-versus-effect split | P (and B for "doubt is never automatically Oppose") | RECOMMENDED (B: REVIEWER-DIRECTED) |
| V6-R3 — `U-CONTEXT` minimum signal; bare agreement as an evidence-based exclusion | H | RECOMMENDED |

**The statuses of P, U and H are deliberately unchanged.** Each row also
contains drafter-designed details the review didn't address. Some examples:
- the dominance signals and the hedge-marker list, in P;
- the post-verification rule, in U;
- the C-codes and the note template, in H.

Re-statusing whole rows would silently promote those details. Whether to
split the confirmed positions into their own REVIEWER-DIRECTED rows is
left for your decision (see the reviewer questions).

## Rule status coverage (X4)

| Rule | Where | Decision | Status |
|---|---|---|---|
| Plausible-in-scope test; uncertain target → proceed as in scope | C1 step 1 | M | REVIEWER-DIRECTED |
| OFF_TOPIC only if no part is in scope; partial-scope labelling | C1 step 2 | M | REVIEWER-DIRECTED |
| Neutral = in scope with no identifiable evaluation; needs engagement with the target | C1 step 4 | L (the engagement requirement restates guidelines §8 mistake 7) | REVIEWER-DIRECTED |
| Unclear = identifiable but unresolvable evaluation; the ambiguity rule | C1 step 5 | L | REVIEWER-DIRECTED |
| Unclear sub-reasons, including the two `U-TARGET` variants | C1 step 5 | H | RECOMMENDED |
| `U-CONTEXT` minimum signal; bare agreement → `TOO_SHORT_NONSUBSTANTIVE`, evidence-based (R3; position reviewer-confirmed, V6-R3) | C1 step 5 | H | RECOMMENDED |
| Target-less Q14 exception to the available-object requirement, with its four limits (position reviewer-confirmed, V6-R1) | C1 step 5; C7 | U | RECOMMENDED |
| Two-component stance target (initiative, process) | C2 | A | RECOMMENDED |
| Participation versus process boundary test | C2 | A | RECOMMENDED |
| Openness-angle test | C2 | N | RECOMMENDED |
| Prompt-referent rule; an unverified referent stays unresolved (R1) | C2 | M | REVIEWER-DIRECTED |
| Recommendation / question / information-request boundaries; grammar rule | C3 | Q | REVIEWER-DIRECTED |
| Bare topics → Neutral | C3 | C | RECOMMENDED |
| Corpus-specific application of D4; hope/doubt never automatically Oppose | C4 | B | REVIEWER-DIRECTED |
| Input definitions; problem-statement test; hedged delivery uncertainty alone → Neutral | C4 | P (removal demands: D) | RECOMMENDED |
| Four-way split: hedged uncertainty / definite future non-delivery / established non-delivery / ineffectiveness (position reviewer-confirmed, V6-R2) | C4 | P | RECOMMENDED |
| Hedge-marker list; rhetorical or unclear cases treated as hedged, at confidence 1 | C4 | P | RECOMMENDED |
| a–d tree; branch d fallback | C4 | O | REVIEWER-DIRECTED |
| Dominance signals and precedence | C4 | P | RECOMMENDED |
| Removal demands / replacement proposals | C4 | D | RECOMMENDED |
| Sarcasm rules | C5 | R | RECOMMENDED |
| Confidence-1 rationale for unresolvable sarcasm | C5 | R (rationale requested in the v2 review) | RECOMMENDED |
| Non-stance negation | C6 | S | RECOMMENDED |
| Q14 rules and limitations; the conservative interim rule for target-less answers (R1) | C7 | U | RECOMMENDED |
| Q13 recovery | C7 | E | OPTIONAL / DEFERRED |
| Note template and tags | C8 | H (template form requested in the v2 review) | RECOMMENDED |
| Needs-review markers, valid states | C9 | J | RECOMMENDED |
| v1 immutability, v2 re-review | C10 | G | REVIEWER-DIRECTED |
| Repeat pass first | Adoption order | F | REVIEWER-DIRECTED |
| Taxonomy preserved; T1 monitoring only | T1 | K | REVIEWER-DIRECTED |
| Unclear-count monitoring report | T1 | V | RECOMMENDED |

## Potential impact on existing annotations

These are estimates from train + validation analyst groupings (n = 213);
the 37 test-split rows were not analysed. **No label is changed or
declared wrong.** All changes go through the logged v2 re-review (C10).

| v1 label | Count | Candidates in v2 re-review | Depends on |
|---|---|---|---|
| Unclear | 66 | ~22 → `OFF_TOPIC`, or Support/Oppose/Neutral where partly in scope; ~35 → Neutral (or an exclusion code if not engaging with the target); ~6–8 stay Unclear (the 2 `U-CONTEXT` candidates only if they name an in-scope subject, otherwise `TOO_SHORT_NONSUBSTANTIVE`, R3); 1 needs a real note | L, M, N, H |
| Support | 78 | 7 "implied support" items and other topic-only items → Neutral or `OFF_TOPIC`; out-of-scope recommendations → `OFF_TOPIC`; process praise depends on A | A, C, N, Q |
| Oppose | 24 | Delivery criticism (11 of these come from Q14) expected to stay Oppose (branch a); items that also propose a fix go to branches c/d. **Target-less Q14 items → Unclear `U-TARGET` until Q13 is verified, under either A outcome (R1).** Q14 Oppose labels that name their own target are unaffected. **V6-R2:** definite future non-delivery is Oppose even without grounding in past failure. v5 already treated definite predictions as non-delivery assertions, so little change is expected. Hedged doubt stays non-Oppose. | A, B, O, P, U |
| Neutral | 45 | Few changes expected; may gain items | L |

**If L is not adopted**, most of the ~35 "no position" Unclear labels
remain correct under the current definitions.

Expected consequences:
- **Class balance.** Unclear shrinks sharply under L. The stance pool
  shrinks by `OFF_TOPIC` exclusions under N (~10%). `U-MIXED` may gain
  "X is useless; do Y" comments under branch d (monitored under V).
- **Comparability.** v2 labels need new splits, and their results aren't
  directly comparable with Experiments 1–3 (macro-F1 0.26–0.33 on v1).
- **Confidence.** v2 confidence-1 counts mean "borderline or
  review-requested" (C9) and aren't comparable with v1's 3
  confidence-1 labels.

## Recommended order of adoption and repeat annotation

1. **Formally decide the RECOMMENDED items** (A, C, D, H, I, J, N, P, R,
   S, U, V) and confirm the REVIEWER-DIRECTED items (B, F, G, K, L, M, O,
   Q). E is deferred and doesn't block adoption. Nothing is adopted until
   then.
2. **Run the pre-registered 38-item repeat pass under the original
   protocol** (F), no earlier than 2026-11-22. Record in the repeat report
   that the annotator has read the error analysis and these proposals, so
   the second pass is not fully naive.
3. **Publish a versioned guideline update** amending the authoritative
   passages listed above. This is a separate documentation task; the
   current documents stay unchanged until then.
4. **Calibrate** on hypothetical worked examples only.
5. **Logged v2 re-review of the 250** (C10). The v1 files are never
   edited.
6. **`annotation_batch_002`** (~400, proportional random) under the adopted
   version, sealed as the new Level 1 test set, with its own hidden 15%
   repeat subset and a 14-day gap.
7. **Only then** create v2 splits and revisit modelling.

---

## Change log: v3 → v4 (historical, carried over from v4)

The terms "dismissal" and "hope/doubt" below are v4 wording. In v5 they
are "ineffectiveness evaluation" and "delivery uncertainty" (R2).

| Area | Change |
|---|---|
| Front matter | Added "Definition changes requiring explicit approval" (L, N) with the list of authoritative passages; corrected v3's claim that no class is redefined. |
| C1 | Step 1 plausible-scope test and uncertain-target route; step 2 OFF_TOPIC only if no part is in scope, plus partial-scope labelling; step 4 requires engagement with the target; `U-TARGET` split into `(target)` and `(direction)`; new examples (partial scope, non-engaging greeting). |
| C2 | Two-component target (initiative including participation; engagement process under A); boundary test; openness-angle test acknowledged as broader (N); prompt-referent rule (M); examples table with outcomes if A is or isn't adopted. |
| C3 | Added replacement/strengthening proposals; a proposal dismissed by its own commenter is not a recommendation. |
| C4 | Input definitions (failure criticism, dismissal, removal demand, recommendation including replacement, praise) and the "neither" category (problem statements, hope/doubt); D4 hope/doubt rule; dominance signals with precedence; Decision D rewritten; all branch examples rebuilt and checked; the process included in failure criticism under A. |
| C5 | Aligned with C1: `U-TARGET (target/direction)`; no plausible in-scope reading → OFF_TOPIC; new uncertain-target example; the Q14 example tagged `prompt-dependent (C2)`. |
| C6 | Example re-attributed to C4 branch a (dismissal). |
| C7 | Q13's object marked unverified; target-named versus target-less Q14 answers; outcomes under A and not-A; documented limitations. |
| C8 | Template and tags; example notes regenerated to match C1–C9. |
| C9 | BORDERLINE / REQUESTED markers with conceptual confidence; table of valid and invalid states; v1 not retroactively invalid. |
| T1 | Count corrected to about 8 plus 1 placeholder; U-MIXED-from-branch-d monitoring (V). |
| Register | New decisions L–V; rule status coverage table; status summary. |

## Finding-resolution table (v3 audit — historical, carried over from v4)

| Finding | Severity | Resolution in v4 | Where |
|---|---|---|---|
| X1 Unclear silently redefined | Critical | **Resolved.** Acknowledged; Decision L (REVIEWER-DIRECTED); authoritative passages listed (including examples CSV UNC-03 and UNC-08). | Front matter; C1; register |
| F1 Uncertain target scope vs scope-first | Critical | **Resolved.** Plausible-in-scope test; uncertain target → proceed as in scope → `U-TARGET (target)`; consistent with D7 and C5. | C1 step 1; C5 |
| F1b Prompt rule vs Q14 | Important | **Resolved.** The prompt may identify a referent, never bring in a subject; tag `prompt-dependent (C2)`; Q14 limits documented. | C2; C7 |
| F2 Undefined "opposite cue"; Decision D bypassing C4 | Critical | **Resolved.** Removal demand and replacement proposal defined; mixed cases go through a–d; `U-TARGET (direction)` only for an unrecoverable purpose; "opposite cue" removed. | C4; register D |
| F3a Conflicting dominance signals | Critical | **Resolved.** S1 > S2/S3; conflicting S1 → d; conflicting S2/S3 → d; no signal → d. | C4 dominance test |
| F3b Branch examples not fitting their branch | Important | **Resolved.** All examples rebuilt and checked against the input definitions; dismissed proposals aren't recommendations; problem statement versus failure criticism test. | C3; C4 examples |
| F4 C9 stored versus conceptual confidence | Important | **Resolved.** BORDERLINE / REQUESTED markers carry the conceptual value; valid/invalid table; wording corrected. | C9; C8 |
| F5a Partial-scope comments | Critical | **Resolved.** OFF_TOPIC only if no part is in scope; label from the in-scope part; tag the ignored part. | C1 step 2; C2 examples |
| F5b Q13 object unverified; A dependency | Important | **Resolved as far as documentation allows.** Assumption removed and marked unverified. Verifying Q13 itself stays deferred (E). **The v4 rule that Decision A resolves target-less Q14 answers is superseded in v5 by the conservative interim rule (R1).** | C7 |
| F5c Participation versus process | Important | **Resolved.** Two-component target; boundary test; process included in C4's definitions under A. | C2; C4 |
| X2 OFF_TOPIC broadened | Important | **Resolved.** Acknowledged as Decision N (RECOMMENDED), with guidelines §5 listed for amendment. The broadening itself remains a substantive choice awaiting approval. | Front matter; C2 |
| X3 D4 hope/doubt example | Important | **Resolved.** Hope/doubt isn't failure criticism; endorsed goal → Support; doubt alone → Neutral at confidence 1. | C4 |
| X4 Rules without a status | Important | **Resolved.** Decisions L–V; rule status coverage table. | Register |
| O1 Minor-caveat citation | Optional | **Resolved.** Cited as D3's principle, as D4 refers to it. | C4 S2 |
| O2 Greetings versus TOO_SHORT | Optional | **Resolved.** Neutral requires engagement with the target; example added. | C1 step 4 |
| O3 T1 count | Optional | **Resolved.** "About 8 plus 1 placeholder". | T1 |
| O4 Missing C7/prompt tag | Optional | **Resolved.** The tag is now `prompt-dependent (C2)` and is applied in C5, C7 and C8. | C5; C7; C8 |
| O5 L183 not-A consequence | Optional | **Resolved.** Every C2 example shows its outcome if A isn't adopted. | C2 |
| O6 Redundant "iff" in C9 | Optional | **Resolved.** Replaced by marker-identifies-the-case wording and the valid-state table. | C9 |

## Unresolved points for reviewer attention (not findings)

1. **Status classification of L, M, O and Q as REVIEWER-DIRECTED.** These
   positions were specified in review instructions (v2 review point 4; v3
   review points 1 and 3; v4 review requirements 2, 3, 5 and 8). If you
   intended them as RECOMMENDED, they should be relabelled.
2. **Branch d and "X is useless; do Y".** Under B + O, a whole-measure
   verdict combined with a fix becomes `U-MIXED` unless the commenter
   signals dominance. This is internally consistent, but it may populate
   Unclear with a common consultation pattern. It is monitored under V, and
   is not changed here because the a–d tree and B are REVIEWER-DIRECTED.
3. **Delivery uncertainty alone → Neutral.** This is a drafter choice
   (Decision P, RECOMMENDED), implementing B's requirement that doubt never
   automatically becomes Oppose. Unclear `U-TARGET (direction)` is a
   defensible alternative if scepticism is treated as an identifiable
   evaluation.
4. **Hedged versus definite non-delivery — position settled in v6.**
   Raised in v5 as a drafter choice, now **reviewer-confirmed (V6-R2)**.
   What remains open is only the drafter-designed hedge-marker list and the
   rule that unclear or rhetorical cases are treated as hedged (see point
   9).
5. **The Q14 interim rule lowers Q14 Oppose and Support yield.** Target-less
   Q14 evaluations become Unclear `U-TARGET` until Q13 is verified (R1,
   reviewer-confirmed V6-R1). That makes Decision E (OPTIONAL / DEFERRED)
   more consequential than before, but its status is unchanged.
6. **Bare agreement → `TOO_SHORT_NONSUBSTANTIVE` — position settled in
   v6.** Reviewer-confirmed (V6-R3) as an evidence-based exclusion.

**New in v6:**

7. **Statuses of P, U and H.** The confirmed positions V6-R1, V6-R2 and
   V6-R3 sit inside decisions that remain RECOMMENDED, because those rows
   also hold unreviewed drafter detail. Should each confirmed position be
   split into its own REVIEWER-DIRECTED row? Nothing was re-statused
   without your instruction.
8. **Target-less Q14 answers with no evaluation (C7 rule 5).** v5 said
   these "are Neutral". v6 makes them follow C1: Neutral if they engage
   with an in-scope subject, otherwise an exclusion code. This removes a
   conflict with C1 step 4, but it changes v5's literal outcome for
   answers like "No particular reason." (v5: Neutral; v6: exclusion).
   Please confirm.
9. **Hedge markers and unclear cases.** Two V6-R2 details are drafter
   choices:
   - the list of hedge markers ("I doubt", "I don't think they'll",
     "probably won't", …);
   - treating rhetorical or unclear forms ("They're not going to do it,
     are they?") as hedged at confidence 1.

   Treating such forms as definite is the alternative. Note that "I don't
   think they'll do it" (hedged, not an input) and "I don't think it will
   change anything" (an ineffectiveness evaluation, Oppose) now differ
   only in what the hedged claim is about. That boundary may be hard to
   apply consistently, so watch it in the next repeat pass.
10. **Pronouns in Q14 answers.** A pronoun with no antecedent ("It's
    terrible.") doesn't name a target, so the answer falls under the
    exception (C1 step 5, limit 2). This is a drafter clarification needed
    to apply V6-R1.
11. **The code name `TOO_SHORT_NONSUBSTANTIVE`.** V6-R3 uses this code for
    a no-evaluable-target exclusion that has nothing to do with length.
    The name may mislead annotators. Renaming a code would change
    Decision K (exclusion codes preserved), so v6 only documents the
    meaning. A rename would need an explicit decision.

---

## Change log: v4 → v5 (historical, carried over from v5)

R1–R3 below are v5's labels. v6 extends them as V6-R1–V6-R3 (see "Change
log: v5 → v6").

Scope: exactly three review findings (R1–R3). **No decision was added or
removed, and no status changed.** Decisions A–V keep their v4 statuses;
only the descriptions of H, M, P and U were extended.

| Finding | Change | Where |
|---|---|---|
| **R1** Q14 target uncertainty | **C2:** added "an unverified referent is not a resolved referent"; no Decision resolves it. **C7 rule 3:** replaced v4's A-dependent handling with a conservative interim rule. Target-less Q14 evaluations are Unclear `U-TARGET (target)` or `U-TARGET (direction)`, confidence 1, `[NEEDS-REVIEW:BORDERLINE]`, tagged `prompt-dependent (C2)` with the note `Q13 object unverified (C7)`, under **either** Decision A outcome. They are never Support, Oppose or `OFF_TOPIC` until Q13 is verified. Added a post-verification rule, inactive until E. Updated the C7 limitations and examples ("Terrible.", new "Great, really pleased."), the C5 "Great job" example, the C8 notes, register rows M and U, rule-coverage rows, the impact table (Oppose row), T1/V monitoring, and the F5b historical row. | C2; C5; C7; C8; register; coverage; impact; T1 |
| **R2** Delivery doubt vs ineffectiveness | **C4:** added a delivery-versus-effect table using D4's own test (*would the concern disappear if fully implemented?*), with three kinds: delivery uncertainty (not an input), non-delivery assertion (failure criticism), ineffectiveness evaluation (unfavourable, hedged or not). Renamed "dismissal" to "ineffectiveness evaluation". Clarified that an S3 discount phrased as ineffectiveness is one input and the signal, counted once. Re-attributed examples: "shelved like the last three" and "heard the same pledge" are non-delivery assertions; "won't change anything" is an ineffectiveness evaluation. Added examples: "They never follow through…", "Even if they publish every contract…", "Good idea, though I doubt they'll do it" (b) versus "Good idea in theory, but even if they do it, it won't change anything" (c → Oppose), and "I'm not sure they'll actually implement…" (Neutral). **C1:** delivery uncertainty is not identifiable evaluative content. **D4 itself is unchanged.** | C1; C2 example; C4; C5 example; C6 example; C8 notes; register P; coverage |
| **R3** `U-CONTEXT` minimum signal | **C1 step 5:** `U-CONTEXT` requires an explicit endorsement or evaluation signal **and** an in-scope subject named in the comment's own text. A resolvable direction gives Support or Oppose instead. Bare agreement with unavailable content → `TOO_SHORT_NONSUBSTANTIVE`, with the reasons why the protocol doesn't justify `U-CONTEXT`. Agreement with an available prompt is ordinary evaluation. Identifiable evaluative content now requires an available object. Added three C1 examples and two C8 notes. Updated register row H, coverage, the authoritative-texts list (guidelines §5 L130; protocol §5 now also H), T1 (≈6–8), and the impact table (Unclear row). | C1; C8; register H; coverage; authoritative texts; T1; impact |
| Housekeeping | Marked the v3 → v4 change log and the v3-audit finding table as historical; updated the reviewer-attention points (3 reworded; 4–6 added). | End matter |

---

## Change log: v5 → v6

Scope: the three positions confirmed in the v6 review (V6-R1–V6-R3), plus
the consistency fixes they required. **No decision was added, removed or
re-statused.** The register still holds 21 decisions (A–V, no T) with
their v5 statuses. Only the descriptions of H, P and U were extended, and
a non-status note recording the confirmations was added under the
register. Nothing is APPROVED.

| Item | Change | Where |
|---|---|---|
| **V6-R1** Target-less Q14 exception | **C1 step 5** states the general available-object requirement explicitly and adds **the only exception**: target-less Q14 evaluations, handled solely by the C7 interim rule (unchanged outcomes: `U-TARGET (target)` or `U-TARGET (direction)` with scope also unresolved; confidence 1; `[NEEDS-REVIEW:BORDERLINE]`; `prompt-dependent (C2)`; `Q13 object unverified (C7)`; regardless of A; never Support, Oppose or `OFF_TOPIC`). There are **four limits**: Q14 only; no named target, where a pronoun with no antecedent doesn't count; an evaluative direction present; Q13 still unverified. It doesn't extend to other prompts, replies to unavailable comments, or bare agreement. **C1 step 1** names the questionnaire context as the source of the plausible in-scope reading for this exception only. **C7 rule 3** cross-references the exception. **C7 rule 5** now defers to C1 for non-evaluative answers (reviewer question 8). Updated register row U, the coverage rows and the reviewer questions. | C1; C7; register U; coverage |
| **V6-R2** Delivery uncertainty vs definite non-delivery | **C4** now uses a four-way table (hedged uncertainty → not an input; definite future non-delivery → failure criticism; established past/present non-delivery → failure criticism; ineffectiveness despite implementation → unfavourable), with the reviewer's examples, the rationale, a hedged-versus-definite marker list, conservative handling of unclear or rhetorical forms, and explicit precedence of D4's problem-statement test. The failure-criticism definition names both non-delivery kinds; definite future non-delivery no longer needs past-failure grounding. **New C4 examples:** "They won't implement…" (a); "Even if… implemented, it won't work" (a); "They never publish… on time; set a… deadline" (b, problem statement); "They never implement their promises. If they want trust, set a legal deadline." (d); "I doubt they'll implement…" (Neutral); rhetorical "…are they?" (Neutral, confidence 1). Re-attributed existing rows: "shelved like the last three" (definite future plus established); "they never follow through" and "heard the same pledge" (established). **C1** lists definite non-delivery as identifiable evaluative content and only *hedged* doubt as not. **C6** gains a hedged-negation versus definite-negation pair. **C8** gains notes for definite future, established, and hedged-alone cases. **C2** example re-attributed. **D4 itself is unchanged.** Updated register row P, coverage (split into three rows), the impact table (Oppose row) and the reviewer questions. | C1; C2; C4; C5; C6; C8; register P; coverage; impact |
| **V6-R3** `U-CONTEXT` and bare agreement | Position kept. **C1** adds that the exclusion is **evidence-based** (the stance target can't be established from available information), not length-based, citing guidelines §5. A long bare agreement is still excluded; a short comment naming an in-scope subject is evaluated normally. **C8** bare-agreement note updated. The proposed authoritative amendments listed in v5 are kept unchanged (guidelines §5 L130; protocol §5 L274–277). Updated register row H, coverage, and the reviewer questions (code-name issue). | C1; C8; register H; coverage |
| History | v1–v5 untouched; the v4 → v5 change log is marked historical; this log is added. The v3 → v4 log and the v3-audit table are unchanged. | End matter |

# Review of the existing Indian annotation codebooks

**Reviewed (read in full, unchanged):**
- `OLD:indian/reports/mygov_annotation_codebook_v1.md` (MyGov, draft for a 50-comment pilot)
- `OLD:indian/reports/tweets_annotation_guidelines_v1.md` (tweets, sentiment pilot)

**Benchmark:** the project objective, a **four-class** stance task (Support / Oppose / Neutral / Unclear) in which stance ≠ sentiment.

**Outcome:** a separate proposal, [PROPOSED_INDIAN_STANCE_CODEBOOK_v2.md](PROPOSED_INDIAN_STANCE_CODEBOOK_v2.md) — **PROPOSED, NOT ADOPTED**.

## 1. What v1 gets right (kept in v2)

- A **single, explicit stance target**: the draft Government Open Data Use License – India and the policy of releasing government data under it. It explicitly excludes government in general, Digital India, Aadhaar, taxes and similar.
- **"Criticism is not opposition":** requests for more or better openness are Support, even when they criticise a clause's wording.
- **Questions are Neutral** unless worded as a position.
- **General praise of the government is not Support** for the licence.
- **Tone is never stance.** The sentiment field is separate.
- **Truncated text** is labelled from what is visible.
- **No machine translation.**
- **No copying of names or emails** into free-text fields.
- **Two independent annotators**, kappa ≥ 0.60, and "only adjudicated labels are ground truth".

## 2. Problems found in the MyGov codebook v1

| # | Finding | Why it matters | v2 proposal |
|---|---|---|---|
| R1 | **Five labels.** `Mixed` is a separate class, but the project objective is four classes. | The label set and the objective disagree. A five-class dataset cannot be silently collapsed later without re-annotation evidence. | Remove `Mixed`. If the commenter's own framing gives a net direction, use it. Otherwise use `Unclear` with `unclear_reason = MIXED`. **Decision D1.** |
| R2 | **Off-topic comments are `Neutral`** (plus a concern code). | This mixes *topic relevance* with *stance*. Neutral becomes a catch-all for "about something else", and a model would learn topic, not stance. | A separate `exclusion_code = OFF_TOPIC`. Neutral is kept for on-target comments with no position. **Decision D2.** |
| R3 | **`Unclear` mixes comprehension failures** (unreadable script, attachment-only, fragments) **with genuine stance ambiguity**. | One class holds unrelated phenomena, which hurts both agreement and modelling. | Exclusion codes `ATTACHMENT_ONLY`, `UNREADABLE` and `NON_SUBSTANTIVE`. `Unclear` only with a recorded reason. |
| R4 | **The annotator's language skill decides the label** ("otherwise `Unclear`, note non-English"). | The same comment gets different labels depending on who reads it. | Annotator-dependent problems become `needs_review = yes, reason LANGUAGE`, and the item is reassigned. They are never a label. |
| R5 | **No rule for amendment requests that add restrictions** (e.g. stronger privacy exemptions). | These are common in licence consultations. v1 could put them under Support, Mixed or Oppose. | A constructive amendment that keeps the licence is Support. Rejecting adoption until the change is made is a conditional, handled by R6. |
| R6 | **No rule for conditional positions** ("acceptable only if…"). | Conditionals were likely to be labelled inconsistently. | Label by net direction toward the draft *as proposed*. Use `Unclear / CONDITIONAL_UNRESOLVED` only when the condition's resolution is unknown. |
| R7 | **Sarcasm and distrust:** v1 says what they are *not* (not Oppose by themselves), but not what they *are*. | It leaves a gap. | Label resolvable sarcasm by its intended direction. Unresolvable → `Unclear / SARCASM_UNRESOLVED`. Distrust with no position → Neutral. |
| R8 | **Missing context** (unsaved replies and attachments, references to earlier comments) is not covered. | Replies were never captured, so this case does occur. | `Unclear / MISSING_CONTEXT` if a position exists but depends on unseen content. Bare agreement with unseen content → `NON_SUBSTANTIVE`. |
| R9 | **No confidence field, and no needs-review flag** | Borderline cases can't be found or adjudicated. | `confidence` (1–3, a property of the label) **and** a separate `needs_review` yes/no with a reason (a workflow request). |
| R10 | **Duplicates are labelled independently** ("do not copy"). | 9 normalised-duplicate groups cover 18 comments. Duplicates in different splits are train/test leakage, and double annotation wastes effort. | Annotate one representative per group. All member IDs are recorded; label propagation is for analysis only. **Decision D3.** |
| R11 | **A `sentiment` field is collected beside stance.** | It costs effort, invites anchoring, and creates a sentiment column that later code could misuse as stance. | Drop it from the stance batch. If it is wanted, collect it in a separate pass. **Decision D4.** |
| R12 | **`evidence_span` copies verbatim text.** | Privacy, since spans may include names; it also inflates the annotation burden. | Not collected in the v2 batch. A short `rationale` in the annotator's own words replaces it. |
| R13 | **Agreement plan covers only overall stance kappa ≥ 0.60** | Overall kappa hides failure on the rare classes (Oppose in the Canadian data was 5–12%). | Also report per-class agreement and the Neutral/Unclear and Neutral/OFF_TOPIC confusion. Re-pilot if any class falls below threshold. |
| R14 | **The decision order is unclear** about when relevance is decided ("about the licence *or government open data*"). | Comments about open data in general (portals, formats, specific datasets) sit at the boundary. | An explicit scope test: in scope if it is about releasing or reusing government data under an open licence, including portals, formats, terms and privacy of released data. Government services in general are `OFF_TOPIC`. |

## 3. Problems found in the tweet guidelines v1

| # | Finding | Consequence |
|---|---|---|
| T1 | **They are sentiment guidelines.** They state that political stance "is **not** labelled here". | No tweet stance methodology exists. Reusing the templates for stance would be wrong. |
| T2 | **No stance target.** Political tweets have no single policy. `target_entity` holds people or parties ("BJP", "Rahul Gandhi"). | Under the project objective, stance is toward a *policy, proposal, initiative or issue*. A person-only or party-only position is not policy stance. **Research decision D5:** which targets count, and whether there is a fixed target list. |
| T3 | **Sentiment labels include `Mixed` and `Unclear`.** | They are not reusable as stance labels even after annotation. Stance ≠ sentiment. |
| T4 | **The locked-test concept is sound,** but the split leaks (6 authors, 2 masked texts, 6 near-duplicates). | Repaired in a PROPOSED v2 plan without touching the locked test ([report](../../reports/TWEET_SPLIT_LEAKAGE_REVIEW.md)). |

A separate, source-specific proposal is in [PROPOSED_TWEET_STANCE_GUIDE_v1.md](PROPOSED_TWEET_STANCE_GUIDE_v1.md). The MyGov codebook is **not** assumed to fit tweets.

## 4. Decisions required before adoption (none taken here)

| ID | Decision | Proposed default |
|---|---|---|
| D1 | Four classes: fold `Mixed` into net direction or `Unclear / MIXED` | Yes; this matches the stated four-class objective |
| D2 | Off-topic comments become an exclusion, not `Neutral` | Yes |
| D3 | Annotate one representative per duplicate group | Yes, keeping member IDs |
| D4 | Remove `sentiment` from the stance batch | Yes; a separate pass only if needed |
| D5 | Tweet stance targets: policy/proposal/initiative/issue only, and how the target list is built | See the tweet guide; needs a research decision |
| D6 | Adopt the v2 codebook, after a 49-item MyGov pilot and agreement check | After rights/ethics clearance |

# PolicyLens — Research Gap Analysis

**Status:** research document, built directly on
[`../literature_review/LITERATURE_REVIEW.md`](../literature_review/LITERATURE_REVIEW.md).
No gap below is claimed novel without citing what the literature review
found and did not find — "do not claim novelty without a sufficiently
thorough literature search" is taken literally: several candidate gaps
below turn out to be **partially** addressed by existing work, and that
finding is reported honestly rather than inflated into a clean research
opening.

For each candidate gap: supporting literature, what's already addressed,
what remains insufficiently addressed, whether PolicyLens can realistically
investigate it, and how it could be evaluated.

---

## 1. Policy-context-aware stance classification

**Supporting literature:** Xie et al. (2023) pairs comment text with a
policy-description target for cross-policy stance transfer; Burnham
(2023, preprint) argues stance detection needs explicit context to be
answerable at all; Ji et al. (2025) proposes a context-aware attention
architecture for target-conditioned stance.

**Already addressed:** the *idea* that stance needs a target/context is
well established (this is stance detection's whole premise since
Mohammad et al. 2016). Xie et al. 2023 shows a concrete architecture for
*policy*-as-target specifically, not just arbitrary social-media targets.

**Insufficiently addressed:** none of the papers found condition on a
**structured, multi-granularity** policy context the way PolicyLens's own
design requires — a specific *section* within a document, not just a
policy-level description. Xie et al.'s "target" is a short policy
description, not a document with addressable sub-sections. The literature
search (Section 1 of the review) also surfaced that this project's own
real corpus has **no formal clause-numbered policy document at all** — the
research gap here is as much about *what counts as policy context when
none is formally structured* as it is about classifier architecture.

**Can PolicyLens realistically investigate this?** Yes, but only after
real annotations exist. `STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md`
experiment 3 (SBERT + classifier) is the natural first step toward
testing whether including `policy_context`/`policy_section` text as part
of the input (vs. comment text alone) measurably changes performance —
this is directly testable as an ablation once a labeled dataset exists,
and is not currently run (no model has been trained).

**Evaluation:** macro-F1 with vs. without policy-context features, on the
same split, same seed — an ablation study, not a new benchmark.

---

## 2. Separating concern identification from stance detection

**Supporting literature:** Cardie et al. (2008, both papers) treat
"issue categorization" as the primary task for e-rulemaking comments,
largely without a parallel stance dimension; the EU stakeholder-
consultation clustering study (DOI 10.1007/s10506-024-09426-6) clusters
by position/opinion grouping, which is closer to combined stance+concern
than to concern alone.

**Already addressed:** issue/topic categorization of public comments
(without stance) is addressed (Cardie et al.); stance detection
(without concern grouping) is extensively addressed (Section 2 of the
review). Clustering by combined "opinion" is also addressed (the EU
study).

**Insufficiently addressed:** **the explicit, enforced independence of
the two pipelines** — grouping comments by concern such that a single
concern group can and does contain multiple stances, with that mixture
reported as a *feature* of the concern group rather than noise to
resolve — does not appear directly in the papers found. The EU
stakeholder study's "opinion clustering" and most consultation-analysis
work found conflates the two (groups positions, not pure topics). This is
the most genuine gap identified in this review: a design (and evaluation)
that *deliberately keeps concern and stance orthogonal* is not clearly
present in the literature search conducted.

**Can PolicyLens realistically investigate this?** Yes — this is already
the project's stated design principle (`SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`'s
"deliberately independent" section), implementable once both pipelines
have real output to cross-reference (clustering needs no stance labels at
all to run; the *analysis* of stance-mixture-within-clusters needs both).

**Evaluation:** report the stance-label distribution within each concern
cluster once both pipelines have run on real data; a cluster that is
stance-homogeneous in every case would be a signal the grouping is
accidentally re-deriving stance rather than concern — an explicit check
this project should run, not just hope passes.

---

## 3. Preserving minority and conflicting public opinions

**Supporting literature:** no paper found in this review directly
addresses "minority opinion preservation" as its own research question
for public comment analysis; Sandri et al. (2023) and the recent
disagreement-as-signal preprints address a related but distinct problem
(annotator disagreement, not respondent-opinion diversity within an
aggregate dataset).

**Already addressed:** HDBSCAN's native noise category (McInnes et al.
2017) at least avoids *forcing* an outlier comment into a cluster it
doesn't belong to, which is a structural precondition for not erasing
unusual views — but this is a side effect of the clustering algorithm's
design, not a paper that studied minority-opinion preservation directly.

**Insufficiently addressed:** nothing found evaluates whether a
summarization or analytics pipeline *systematically under-represents*
minority stances or concerns within a policy report. This is a real,
citable gap — the closest adjacent finding (Ji et al. 2023's hallucination
survey) is about generative accuracy, not representational fairness
across viewpoint frequency.

**Can PolicyLens realistically investigate this?** Partially, and later.
It requires real stance + concern-cluster data at a scale large enough to
have genuine minority viewpoints (the current 250-item pilot batch is too
small to study this meaningfully — see `RESEARCH_LIMITATIONS.md`). It is
a legitimate direction for the full eligible corpus (7,941+ comments)
once annotation tooling and a classifier both exist.

**Evaluation:** compare the stance distribution *within* each policy
report's representative-comment selections against the full distribution
in that report's underlying comments — representative comments should
not systematically exclude the minority stance within a group.

---

## 4. Evidence-grounded concern-group summarization

**Supporting literature:** FactCC (Kryściński et al. 2020), SummaC (Laban
et al. 2022), and the hallucination survey (Ji et al. 2023) establish
both the problem (abstractive summaries can be unfaithful) and automatic
detection methods.

**Already addressed:** faithfulness *detection* for generic abstractive
summarization is a mature sub-field (multiple benchmarks, several
methods). PEGASUS (Zhang et al. 2020) shows strong low-resource abstractive
performance is achievable from relatively few examples.

**Insufficiently addressed:** applying these faithfulness checks
specifically to **short, informal public-comment text as source material**
(rather than news articles, which is what FactCC/SummaC/PEGASUS were all
evaluated on) is not demonstrated in anything found here. Public comments
are noisier, shorter, and more colloquial than news text — whether
faithfulness-detection methods trained/validated on news transfer to this
domain is an open, evaluable question.

**Can PolicyLens realistically investigate this?** Only as future work —
the current plan (`SYSTEM_ARCHITECTURE.md` component 9) deliberately
scopes out abstractive summarization for now, defaulting to extractive
summaries precisely because this gap is unresolved. This is honestly
reported as a reason for current scope-narrowing, not spun as something
PolicyLens already solves.

**Evaluation (for future work):** apply SummaC or FactCC-style scoring to
any future abstractive concern-group summary, with a held-out
human-rated faithfulness sample as ground truth — exactly the evaluation
framework already specified in
`../experiments/EXPERIMENT_EVALUATION_FRAMEWORK.md`'s summarization
section, ready for whenever this future work is explicitly scoped.

---

## 5. Traceability from generated summaries back to original comments

**Supporting literature:** FactCC's auxiliary span-extraction task is the
closest found precedent (locating a supporting source span for a factual
claim); no paper found addresses comment-to-aggregate-output traceability
as a system design requirement end-to-end (ingestion through
summarization through reporting).

**Already addressed:** source-attribution as a *sub-task within
faithfulness evaluation* is addressed (FactCC). Full-pipeline
traceability as a first-class system design requirement is not something
this review found addressed as its own research contribution anywhere.

**Insufficiently addressed:** a formal schema-level guarantee (every
aggregate output resolvable back to source comment IDs) as described in
`DATA_MODEL.md`'s "traceability guarantees" section does not appear to be
a named, evaluated research contribution in the literature found — it
exists as an implicit property of extractive methods, not as something
explicitly designed and tested for compound pipelines (classification +
clustering + summarization together).

**Can PolicyLens realistically investigate this?** Yes — this is already
implemented as a design principle (`DATA_MODEL.md`) and partially
implemented in code today
(`ml/stance_classification/validate_splits.py`'s independent re-validation
pattern is the methodological template; a full traceability-integrity
checker for the whole pipeline is proposed but not yet built, since the
downstream components it would check don't exist yet).

**Evaluation:** an automated integrity check (as specified in
`SYSTEM_ARCHITECTURE.md` component 11) that every `Summary`,
`PolicyReport`, and `ConcernGroup` reference resolves to a real,
retrievable comment — reported as a pass/fail structural audit, not a
statistical metric.

---

## 6. Privacy-preserving and quality-aware public feedback datasets

**Supporting literature:** none of the three literature searches
conducted for this review specifically targeted privacy-preservation
methods (the search topics were stance/clustering/summarization-focused,
per the task's own topic list) — this is reported honestly as **a gap in
this review's own search coverage**, not a confirmed gap in the field.

**Already addressed (from general awareness, not from this review's
searches):** PII detection/redaction is a broad, well-established NLP
sub-field independent of the public-comment domain; this review did not
verify specific papers applying it to public-consultation data.

**Insufficiently addressed:** whether existing PII-redaction methods
perform adequately on the specific noisy, informal register of public
comments (vs. the more formal text such methods are usually validated on)
is not confirmed either way by this review.

**Can PolicyLens realistically investigate this?** Only with a properly
scoped, separate literature search first — this document should not claim
a gap exists here with the same confidence as gaps 1–5, precisely because
the underlying search wasn't done. `SYSTEM_ARCHITECTURE.md` component 3
(data validation and privacy filtering) is designed with flag-for-review
semantics specifically because this uncertainty is real, not resolved.

**Evaluation:** deferred — requires the missing literature search before
an evaluation framework can be responsibly proposed.

---

## 7. Multilingual and underrepresented citizen feedback

**Supporting literature:** none of the three literature searches directly
targeted multilingual stance/clustering methods; this is the same honest
gap-in-search-coverage caveat as item 6.

**Already addressed:** SBERT has documented multilingual variants (noted
in `SEMANTIC_GROUPING_EXPERIMENT_PLAN.md` and
`STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md` as an option), but this review
did not verify specific multilingual-stance-detection papers.

**Insufficiently addressed:** unknown — not searched in this pass.

**Can PolicyLens realistically investigate this?** Yes, concretely and
soon, independent of any further literature search: the project's own
corpus already has a real, quantified French-language subset (1,078 of
10,043 comments, ~10.7%, per `SINGLE_ANNOTATOR_PROTOCOL.md` section 10)
that is explicitly out of scope for the current English-only pilot batch
pending confirmation of the annotator's French proficiency. This is a
concrete, actionable, already-identified next step, not a hypothetical
research direction.

**Evaluation:** once a French-language batch is annotated (same
methodology as `SINGLE_ANNOTATOR_PROTOCOL.md`, re-run with a multilingual
embedding model for any clustering/classification use), compare
performance and intra-annotator consistency against the English batch —
the same kappa-based method already used, applied to a second,
independently-sampled language subset.

---

## Summary table

| Gap | Genuinely under-addressed in literature found? | PolicyLens can investigate now? |
|---|---|---|
| 1. Policy-context-aware stance classification | Partially (structured multi-section context not found) | Yes, once annotations exist |
| 2. Separating concern from stance | **Yes — the strongest gap found** | Yes, design already in place |
| 3. Preserving minority opinions | Yes, not directly studied | Partially, needs larger-scale data |
| 4. Evidence-grounded concern summarization | Yes, domain-transfer question open | Only as explicitly scoped future work |
| 5. End-to-end summary traceability | Yes, as a named design requirement | Yes, partially implemented already |
| 6. Privacy-preserving feedback datasets | **Not actually assessed — search gap, not field gap** | Not yet — needs its own literature search |
| 7. Multilingual/underrepresented feedback | **Not actually assessed — search gap, not field gap** | Yes — concrete next step already identified |

# PolicyLens — Proposed Research Contributions

**Status:** synthesis document. Lists this project's proposed (not yet
realized — no experiment has produced a result) contributions, each tied
to a specific gap from
[`../research/research_gaps/RESEARCH_GAP_ANALYSIS.md`](../research/research_gaps/RESEARCH_GAP_ANALYSIS.md)
and a specific research question from
[`../research/methodology/RESEARCH_QUESTIONS_AND_HYPOTHESES.md`](../research/methodology/RESEARCH_QUESTIONS_AND_HYPOTHESES.md).
None of these is claimed as a finding — each is a contribution this
project is positioned to make, pending the work that's already planned.

## Proposed contributions

1. **An explicit, enforced separation between concern identification and
   stance detection in public-comment analysis** (addresses gap 2, the
   strongest gap identified in the literature review — most comparable
   consultation-analysis work found conflates "opinion clustering" with
   topic clustering). PolicyLens's architecture makes this separation a
   structural property (`SYSTEM_ARCHITECTURE.md`'s design principle,
   `DATA_MODEL.md`'s schema), not an incidental choice, and RQ2 gives it
   a concrete evaluation (does clustering actually preserve stance
   diversity within groups, measured directly).

2. **A documented methodology for adapting policy-context requirements
   (rule D6) to a real corpus that has no formal, clause-numbered policy
   document** (`SINGLE_ANNOTATOR_PROTOCOL.md` section 5) — most stance-
   detection work assumes a clean target description (Xie et al. 2023's
   "policy description" or a tweet's named target); this project's actual
   data is messier (survey-question-level context, event/theme metadata)
   and the methodology for working with that reality, rather than
   assuming it away, is itself a documented, transferable contribution.

3. **A rigorous, honestly-scoped single-annotator reliability
   methodology** — intra-annotator (test-retest) kappa with a hidden,
   blind, 14-day-gapped repeat subset, an explicit low-sample-size
   warning built into the kappa computation itself
  (`scripts/annotation/repeat.py`), and a hard refusal (in code, not just
  policy) to call any dataset gold-standard before that check clears a
  stated bar. This directly operationalizes the disagreement-and-
  reliability literature (Landis &amp; Koch 1977; Artstein &amp; Poesio
  2008; Sandri et al. 2023) for the specific, under-discussed case of a
  single-annotator project, rather than assuming multi-annotator
  agreement methodology transfers unchanged.

4. **A schema-level, independently-auditable traceability guarantee**
   spanning ingestion through summarization (`DATA_MODEL.md`'s
   traceability guarantees; RQ4's integrity-checker design, modeled on
   `ml/stance_classification/validate_splits.py`'s existing re-validation
   pattern) — addresses gap 5, where the literature found source-span
   attribution only as a sub-task within faithfulness evaluation
   (FactCC), not as a named, pipeline-wide design requirement.

5. **An extractive-first, evidence-grounded summarization default**,
   explicitly deferring abstractive summarization until a faithfulness-
   evaluation methodology for short, informal public-comment text (as
   opposed to the news-text domain FactCC/SummaC/PEGASUS were validated
   on) is separately scoped (gap 4) — a disciplined scope decision
   documented as such, not a workaround presented as a finished solution.

## What would make each contribution real (not yet done)

| Contribution | Still required |
|---|---|
| 1. Concern/stance separation | Finished annotation + a clustering run + the RQ2 cross-tabulation |
| 2. Adapted policy-context methodology | Already real as *methodology*; RQ1's ablation would test its classification value |
| 3. Single-annotator reliability methodology | The actual 38-item repeat pass (gated on the 14-day wait) |
| 4. Traceability integrity checker | Building the checker (can start now, per RQ4) + downstream components (clustering, summarization) to check against |
| 5. Extractive-first summarization | Implementing representative-comment selection + extractive summary assembly (not yet built) |

## Readiness for the next development phase

- **Annotation subsystem:** implemented, tested (120 automated tests),
  audited for real-use edge cases, and **in active use** — genuine
  annotation progress exists in the real batch as of this writing.
- **ML dataset preparation:** implemented and tested against synthetic
  fixtures; correctly refuses to run against anything but a genuine
  finalized export.
- **Research foundation:** a verified (not fabricated) literature review,
  a gap analysis that honestly separates "under-addressed in the
  literature found" from "not actually searched yet," a falsifiable set
  of research questions with explicit blocked/unblocked status, and a
  full evaluation framework defined before any result exists to
  evaluate.
- **System architecture:** a 14-component design with explicit
  responsibilities/schemas/error-handling per component, and Mermaid
  diagrams for both the proposed full system and the subset that's
  actually implemented today — kept visibly distinct from each other
  throughout, not blurred together.
- **Not ready yet, and correctly so:** any model-training phase. No
  classifier, no clustering run, no summarizer exists, because the one
  genuine blocker — a complete, validated, single-annotator dataset — is
  still in progress. Every piece of tooling this phase built is designed
  to make that transition immediate and low-risk once annotation (and its
  14-day-gapped reliability check) finishes, rather than requiring
  further design work under time pressure once real data exists.

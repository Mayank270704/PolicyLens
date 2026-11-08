# ML Integration Guide

`backend/app/ml_interfaces/` defines five abstract contracts so the API,
database, and tests can all be built and exercised **today**, before any
real model exists, and so a trained component can be wired in **later**
without redesigning anything around it.

## The five interfaces

| Interface | File | Real implementation exists today? |
|---|---|---|
| `StanceClassifier` | `stance_classifier.py` | No — `NotYetTrainedStanceClassifier` raises `MLComponentNotImplemented`. See `docs/experiments/STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md`. |
| `EmbeddingProvider` | `embedding_provider.py` | No — `NotYetConfiguredEmbeddingProvider` raises. Loading any real model (e.g. `all-MiniLM-L6-v2`) must be explicit, never implicit, since it can trigger a one-time download. |
| `ConcernGrouper` | `concern_grouping.py` | No — `NotYetConfiguredConcernGrouper` raises. See `docs/experiments/SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`. Signature deliberately takes embeddings only, never a stance label — the independence principle enforced at the interface level. |
| `RepresentativeSelector` | `representative_selector.py` | **Yes** — `CentroidSimilarityRepresentativeSelector` is a real, working implementation (cosine similarity to the group centroid). It needs no trained model and fabricates nothing, just arithmetic over embeddings the caller supplies. |
| `Summarizer` | `summarizer.py` | **Yes, for extractive** — `ExtractiveSummarizer` assembles representative comments verbatim (100% evidence coverage by construction). `NotYetConfiguredAbstractiveSummarizer` raises — abstractive summarization is explicitly out of scope until a faithfulness-evaluation methodology is separately scoped (`research/research_gaps/RESEARCH_GAP_ANALYSIS.md` gap 4). |

## Why placeholders raise instead of returning something

Every `NotYetConfigured*`/`NotYetTrained*` class raises
`MLComponentNotImplemented` rather than returning a hardcoded, random, or
otherwise fabricated result. This is a hard project-wide constraint ("do
not fabricate model predictions") enforced at the type level: there is no
code path in this backend that can silently substitute a fake prediction
for a real one. A caller either gets a real result or an explicit,
catchable error — never a convincing-looking guess.

## Wiring in a real implementation (future work, not done yet)

1. Implement the interface (e.g. `class TfidfLogRegClassifier(StanceClassifier): ...`)
   following the experiment design it corresponds to.
2. Construct a `ModelVersion` row recording its name/version/config/
   `source_data_hash` (see `docs/backend/DATABASE_SCHEMA.md`).
3. Inject the concrete instance wherever the interface type is currently
   used (FastAPI's `Depends()` is the natural mechanism — no router code
   in this backend currently depends on a concrete ML class, only on the
   abstract interface types, so this swap touches one wiring point, not
   every call site).
4. Any `StancePrediction`/`Summary` the new component produces must set
   `source="model"` / `method="abstractive"` and the corresponding
   `model_version_id` — enforced by the database's own `CHECK`
   constraints (see `DATABASE_SCHEMA.md`), so this isn't optional.

## Relationship to the annotation subsystem

Human-sourced `StancePrediction` rows (`source="human"`) are the only
kind that exist in a production flow until a classifier is trained and
validated. The actual source of human stance judgments right now is
`scripts/annotation/` (the CSV-based single-annotator tool), entirely
separate from this database — see `docs/backend/SETUP_GUIDE.md`'s note on
why these two systems don't share storage. A future, explicitly-scoped
step would import a `finalize.py` export into `Comment` +
`StancePrediction` rows here; that importer does not exist yet (there is
nothing finalized to import while annotation is still in progress).

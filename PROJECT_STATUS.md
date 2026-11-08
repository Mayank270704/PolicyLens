# Project Status

| Workstream              | Status      |
|--------------------------|-------------|
| Project initialization   | In progress |
| Dataset audit            | Pending     |
| Research review          | Pending     |
| ML methodology           | Pending     |
| Stance classification    | Methodology finalized; annotation tooling, ML dataset-prep architecture, and experiment plan complete; human annotation not yet started (0/250); no model trained |
| Semantic grouping        | Experiment plan complete (clustering architecture designed, independent of stance); no clustering run yet |
| Summarization            | Pending     |
| ML integration           | Backend foundation + abstract ML interfaces implemented; no model wired in yet |
| Website                  | Deferred (backend API foundation now implemented; frontend itself still not started) |

## Notes

- Stance classification: methodology document drafted at
  [`research/methodology/STANCE_CLASSIFICATION_GUIDELINES.md`](research/methodology/STANCE_CLASSIFICATION_GUIDELINES.md)
  (superseded label-taxonomy note: see
  [`docs/dataset/STANCE_LABEL_DEFINITIONS.md`](docs/dataset/STANCE_LABEL_DEFINITIONS.md)
  for the finalized four-label taxonomy, which drops the earlier "Mixed"
  category into "Unclear").
- **Single-annotator annotation experiment:** methodology, sampling design,
  and tooling are complete; see
  [`docs/dataset/SINGLE_ANNOTATOR_PROTOCOL.md`](docs/dataset/SINGLE_ANNOTATOR_PROTOCOL.md)
  and [`docs/dataset/ANNOTATION_WORKFLOW.md`](docs/dataset/ANNOTATION_WORKFLOW.md).
  A 250-item stratified batch (`data/annotations/new_experiment/annotation_batch_001.csv`)
  and a hidden 38-item repeat subset for intra-annotator reliability
  (`repeat_annotation_plan.json`) are generated and validated. The GUI
  (`scripts/annotation/gui.py`) was audited for save/resume/filter/overwrite
  edge cases, two real bugs were found and fixed (no way to clear a
  mis-set annotation; the filtered Pending/Completed/Excluded navigation
  list going stale immediately after a save), and annotation-time tracking
  was added (`scripts/annotation/timing.py`). A consolidated quality report
  (`scripts/annotation/evaluate.py`) ties stance/exclusion/confidence
  distributions, completion-by-stratum, intra-annotator kappa, and timing
  into one view. **No comment has been labeled yet (0/250).** This is a
  single-annotator design — no inter-annotator agreement is or will be
  claimed — and no dataset here is described as gold-standard prior to the
  intra-annotator consistency check (see
  [`docs/dataset/EXPERIMENT_STATUS_REPORT.md`](docs/dataset/EXPERIMENT_STATUS_REPORT.md)
  for current status).
- **ML dataset preparation architecture** (Phase C) is implemented and
  tested at `ml/stance_classification/dataset_prep.py` (load -> separate
  labels from exclusions -> normalize text into a new column, never
  overwriting source text -> group-aware, stratified, leakage-safe
  train/val/test splitting -> reproducibility manifest with source-file
  hash) plus an independent `validate_splits.py` auditor. It refuses to
  run until a genuine finalized annotation export exists — nothing has
  been prepared from real data yet, since none exists.
- **Model experiment plans** (Phase D/E) are written but not executed:
  [`docs/experiments/STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md`](docs/experiments/STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md)
  (TF-IDF+LogReg, TF-IDF+LinearSVC, SBERT+classifier, and a conditional
  transformer fine-tuning experiment) and
  [`docs/experiments/SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`](docs/experiments/SEMANTIC_GROUPING_EXPERIMENT_PLAN.md)
  (SBERT embeddings -> UMAP where justified -> HDBSCAN primary / K-Means
  comparison -> noise handling -> representative-comment summaries,
  deliberately independent of stance labels). Hardware feasibility
  (8.24 GB RAM, 12 CPU cores, no GPU, all needed packages already
  installed) is assessed in
  [`docs/experiments/HARDWARE_FEASIBILITY_REPORT.md`](docs/experiments/HARDWARE_FEASIBILITY_REPORT.md),
  the full ordered sequence with go/no-go gates in
  [`docs/experiments/ML_EXPERIMENT_ROADMAP.md`](docs/experiments/ML_EXPERIMENT_ROADMAP.md),
  and a consolidated honest limitations list in
  [`docs/experiments/RESEARCH_LIMITATIONS.md`](docs/experiments/RESEARCH_LIMITATIONS.md).
- **Test suite:** 120 automated tests passing
  (`tests/unit/`, `tests/integration/`), covering annotation validation,
  progress/timing/consolidated-evaluation reporting, repeat-gate/blinding/
  kappa logic (fixture data only — no fabricated second annotation round),
  GUI save/resume/overwrite/clear/filter behavior, CSV round-trip edge
  cases (embedded newlines/quotes, atomic-write integrity), and ML
  dataset-split leakage prevention.
- No model has been selected, trained, or evaluated on this or any other
  dataset in this project. No dependency was installed to do any of the
  above — `scikit-learn`, `sentence-transformers`, `torch` (CPU build),
  `transformers`, `umap-learn`, and `hdbscan` were already present in the
  environment and were only inspected, never exercised to train or
  download anything new.
- **Research foundation and system architecture:** a verified literature
  review (every citation confirmed via live search, nothing invented —
  [`research/literature_review/LITERATURE_REVIEW.md`](research/literature_review/LITERATURE_REVIEW.md),
  with comparative-analysis tables included), an honest research-gap
  analysis that distinguishes gaps genuinely under-addressed in the
  literature found from topics this review simply didn't search yet
  ([`research/research_gaps/RESEARCH_GAP_ANALYSIS.md`](research/research_gaps/RESEARCH_GAP_ANALYSIS.md)),
  four falsifiable research questions with explicit blocked/unblocked
  status against annotation completion
  ([`research/methodology/RESEARCH_QUESTIONS_AND_HYPOTHESES.md`](research/methodology/RESEARCH_QUESTIONS_AND_HYPOTHESES.md)),
  a 14-component system architecture with Mermaid diagrams distinguishing
  implemented-today from proposed-future
  ([`docs/architecture/SYSTEM_ARCHITECTURE.md`](docs/architecture/SYSTEM_ARCHITECTURE.md),
  [`DATA_FLOW.md`](docs/architecture/DATA_FLOW.md),
  [`DATA_MODEL.md`](docs/architecture/DATA_MODEL.md)), a full evaluation
  framework for all three ML tasks including summarization (newly defined
  here) ([`docs/experiments/EXPERIMENT_EVALUATION_FRAMEWORK.md`](docs/experiments/EXPERIMENT_EVALUATION_FRAMEWORK.md)),
  a consolidated methodology document including a new ethical-
  considerations section
  ([`research/methodology/PROPOSED_RESEARCH_METHODOLOGY.md`](research/methodology/PROPOSED_RESEARCH_METHODOLOGY.md)),
  and a proposed-contributions summary
  ([`docs/RESEARCH_CONTRIBUTIONS.md`](docs/RESEARCH_CONTRIBUTIONS.md)).
  No research novelty is claimed without the literature search that would
  support it; several candidate gaps are explicitly reported as
  "not actually assessed" rather than inflated into confirmed findings.
- **Backend foundation (new):** a working FastAPI + SQLAlchemy backend
  under `backend/app/` — 12 database tables implementing
  `docs/architecture/DATA_MODEL.md`'s 11 entities (with DB-level
  constraints enforcing stance-label/exclusion mutual exclusivity and
  "a model prediction must record which model"), 15 REST endpoints
  covering policy/document/comment/stance/concern-group/summary/report
  retrieval with pagination and consistent error handling, a document-
  ingestion pipeline (file validation, `.txt`/`.html`/`.pdf` text
  extraction via already-installed `pypdf`/`beautifulsoup4`, heuristic
  section identification, append-only versioning), five abstract ML
  interfaces (`backend/app/ml_interfaces/`) that raise explicitly rather
  than fabricate a prediction, and a PII-flagging heuristic that
  explicitly disclaims being a certified anonymization guarantee. Full
  docs at [`docs/backend/`](docs/backend/) (setup, database schema, API
  reference, ML integration guide, developer guide). 70 new tests (190
  total) using only synthetic fixtures and an isolated in-memory test
  database — nothing in this phase touches `data/annotations/` or the
  real default backend database file. No new dependency was installed:
  FastAPI, SQLAlchemy, Pydantic, Uvicorn, Alembic, pypdf, and
  BeautifulSoup were already present in the environment.
- **Data ingestion, retrieval, and analytics foundation (new):**
  - **Database migrations:** Alembic configured (`alembic.ini` +
    `backend/migrations/`), one clean initial migration, verified
    upgrade/downgrade/re-upgrade and data-preservation across a real
    additive schema change (see `docs/backend/MIGRATIONS_GUIDE.md`).
    While doing this, found and fixed a genuine SQLite/PostgreSQL
    divergence — enum columns were rendering as native PostgreSQL
    `CREATE TYPE` types vs. plain `VARCHAR` on SQLite — now unified via
    `native_enum=False`, locked in by a regression test
    (`docs/backend/DATABASE_COMPATIBILITY.md`). No live PostgreSQL
    server was available to test against; this is stated explicitly
    rather than assumed.
  - **Bulk import/export:** CSV comment ingestion with schema validation,
    batch processing, per-row transaction isolation, and two distinct
    kinds of duplicate handling (idempotent re-import vs. genuine
    duplicate-text multiplicity) — plus a CSV export. An annotation
    import adapter consumes `finalize.py`'s exact output schema,
    independently re-validating every row rather than trusting
    "finalized" at face value; tested only against synthetic fixtures
    (no finalized export exists yet). Every import is persisted as an
    audit-log `ImportRun` row.
  - **Retrieval:** a from-scratch Okapi BM25 implementation (no new
    dependency — neither `rank_bm25` nor `whoosh` is installed) over
    policy sections, with provenance on every result and an explicit
    disclaimer that no retrieval accuracy is claimed (no evaluation
    dataset exists). Statically verified independent of stance
    classification.
  - **Analytics:** descriptive endpoints (comments by source/language,
    submission timeline, data-quality stats, stance/concern-group
    figures) where every stance/concern-group number is paired with an
    `*_available` flag distinguishing "pipeline hasn't run" from
    "genuinely zero" — no fabricated distribution is ever possible.
  - **Privacy/access control:** a role-based authorization interface
    (not yet backed by real authentication — documented explicitly),
    data-retention candidate identification (reports only, never
    deletes), and a schema-level `SubmitterContact` table kept
    structurally separate from every research/export code path. Full
    status of what's implemented vs. requires deployment configuration:
    `docs/backend/PRIVACY_AND_ACCESS_CONTROL.md`.
  - **Tests:** 50 new tests (240 total), including a full synthetic
    end-to-end workflow (create policy → upload document → retrieve
    sections → bulk-import comments → validate → analytics → export →
    audit log) and a second workflow for the annotation-import adapter.
    One real serialization bug was found and fixed during this work
    (a retrieval response schema missing `from_attributes=True`).

# PolicyLens

PolicyLens is an AI/ML-based public policy feedback analysis system. It allows
the public to submit comments on uploaded government policy documents, and
processes those comments at scale to surface structured, analyzable insight
for policymakers and researchers.

## Objective

Given thousands to hundreds of thousands of public comments on a policy
document, PolicyLens aims to:

1. Classify each comment into one of four stance categories: **Support**,
   **Oppose**, **Neutral**, or **Unclear**.
2. Group semantically similar comments that express the same underlying
   concern or idea.
3. Generate a representative summary for each group.
4. Preserve all original comments alongside their individual stance
   predictions.
5. Generate statistics and analytical outputs for each policy.

## Intended ML workflow

```
raw comments -> preprocessing -> embeddings -> stance classification
                                             -> semantic grouping -> summarization
                                             -> evaluation & statistics
```

Each stage is being developed as an independent, testable module under `ml/`,
orchestrated eventually by `ml/pipeline/`.

## Project structure

- `ml/` — ML pipeline modules (preprocessing, embeddings, stance
  classification, semantic grouping, summarization, evaluation, pipeline
  orchestration).
- `data/` — raw, processed, annotated, and sample datasets (raw/processed are
  git-ignored; see `.gitignore`).
- `research/` — literature review, methodology notes, identified research
  gaps, and experiment write-ups.
- `models/` — trained model artifacts (embeddings, stance, clustering);
  weights are git-ignored.
- `notebooks/` — exploratory analysis notebooks.
- `tests/` — unit, integration, and evaluation tests.
- `configs/` — configuration files for pipeline stages.
- `docs/` — architecture, dataset, and experiment documentation.
- `backend/` — application backend (not yet implemented).
- `frontend/` — web frontend (not yet implemented).
- `scripts/` — utility and automation scripts.

## Current development stage

The project is in its **initialization phase**: directory structure, git
configuration, and documentation scaffolding only. No ML models, datasets, or
frontend/backend application code have been implemented yet. See
[`PROJECT_STATUS.md`](PROJECT_STATUS.md) for the current status of each
workstream.

## Development constraints

- Python is the primary ML language.
- Developed primarily on Windows, with CPU execution as the baseline and
  optional GPU acceleration where available.
- Local development machine has 8 GB RAM; dependencies and models are chosen
  to respect that constraint.
- Prefer free and open-source tools; avoid unnecessary dependencies.

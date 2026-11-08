# Hardware Feasibility Report

**Scope:** what this project's actual development machine can and cannot
reasonably run, measured against the model experiments proposed in
[`STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md`](STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md)
and [`SEMANTIC_GROUPING_EXPERIMENT_PLAN.md`](SEMANTIC_GROUPING_EXPERIMENT_PLAN.md).
This is an inspection/planning document — **no model was downloaded,
trained, or run as part of producing it.**

## Measured environment (this machine, inspected 2026-11-08)

| Resource | Value |
|---|---|
| RAM | 8.24 GB total |
| CPU | 12 logical cores |
| GPU | None — PyTorch installed is the CPU-only build (`torch==2.8.0+cpu`) |
| OS | Windows 11 |
| Python | 3.13.7 |

## Packages already installed (none installed for this report — verified present)

| Package | Version | Relevant to |
|---|---|---|
| `scikit-learn` | 1.9.0 | TF-IDF baselines, KMeans, train/test utilities |
| `numpy` | 2.5.3 | everything numeric |
| `pandas` | 3.0.5 | tabular handling (this project's scripts use the stdlib `csv` module directly, not pandas, to stay dependency-light — see `scripts/annotation/schema.py`) |
| `scipy` | 1.17.1 | sparse TF-IDF matrices, stats |
| `sentence-transformers` | 5.7.0 | SBERT embeddings (classification feature #3, clustering) |
| `torch` | 2.8.0+cpu | backend for `sentence-transformers` / `transformers`, CPU-only |
| `transformers` | 4.57.1 | transformer fine-tuning (classification feature #4) |
| `umap-learn` | 0.5.12 | dimensionality reduction before clustering |
| `hdbscan` | present | density-based clustering |
| `matplotlib` | 3.10.5 | cluster/eval visualization |

Not installed: `nltk`, `spacy`. Neither is required by any plan in this
document — `sentence-transformers`' own tokenizers cover the embedding
path, and no plan here calls for classic NLP pipelines (POS tagging, NER,
etc.). If a future need arises, flag it explicitly before installing,
per this project's "avoid unnecessary dependencies" convention.

**No new dependency was installed to produce this report or either
experiment plan.** Package availability above was checked with plain
`importlib.import_module` — no downloads triggered.

## Feasibility per planned experiment

| Experiment | CPU feasible? | Est. peak RAM | Notes |
|---|---|---|---|
| TF-IDF + Logistic Regression | Yes, trivially | < 200 MB | Seconds to fit on hundreds-to-low-thousands of rows. |
| TF-IDF + LinearSVC | Yes, trivially | < 200 MB | Same order as above. |
| Sentence-BERT embeddings (`all-MiniLM-L6-v2`) + classifier | Yes | ~400–600 MB (model ~90 MB on disk, working set larger) | Embedding **extraction** (inference, not training the SBERT model itself) is fast on CPU for hundreds of short comments — seconds to low minutes. The downstream classifier (logistic regression / linear SVM on top of embeddings) is negligible. |
| Transformer fine-tuning (e.g. `distilbert-base-uncased`) | Technically possible, **not recommended at this dataset size** | 2–4+ GB during training, spikes higher with larger batch/sequence length | See the dedicated caveat below — this is the one experiment where hardware is the limiting factor, not just slow. |
| UMAP dimensionality reduction | Yes | Low (depends on embedding count, hundreds-to-low-thousands rows is trivial) | |
| HDBSCAN / KMeans clustering | Yes | Low | Standard CPU clustering libraries, fine at this corpus scale (10,043 texts total, a few hundred to a few thousand embedded at a time). |

### Why transformer fine-tuning is feasibility-marginal here, not a hard no

8 GB RAM is enough to **load** a small transformer (DistilBERT-sized,
~66M params) and run a short fine-tuning loop on a small batch size (e.g.
8–16) and modest sequence length (the corpus's own word-count distribution
puts the 95th percentile at 74 words — short sequences help). It is not
enough to fine-tune a larger model (base BERT/RoBERTa-sized or above)
comfortably alongside a normal desktop workload, and CPU-only training
is slow regardless of whether it technically fits in memory — a handful
of epochs over even a few hundred examples can take tens of minutes to
hours on CPU with no GPU acceleration, which is a workflow problem as much
as a memory one. See `STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md`
experiment 4 for the explicit, conditional recommendation ("only if
hardware and dataset size justify it" — the project's own instruction,
and the honest answer at a ~250-ish single-annotator dataset size is
**not yet**, with a clear path to revisit on a GPU-equipped machine, e.g.
a college lab, per the project's own stated option).

## General hardware-respecting practices this project follows / should follow

- **Batch processing, not whole-corpus-in-memory-at-once**, when embedding
  more than a trivial number of texts — `sentence-transformers`'
  `.encode()` supports a `batch_size` argument for exactly this.
- **Load one large model at a time.** Never hold an SBERT model and a
  transformer classifier in memory simultaneously unless a specific
  comparison experiment requires it, and even then, prefer loading,
  using, and releasing (`del model; gc.collect()`) sequentially over
  concurrent residency.
- **Cache embeddings to disk** (`.npy` or similar) once computed, rather
  than re-running encoding on every analysis pass — this project's
  `ml/embeddings/` directory is reserved for exactly this.
- **GPU execution stays optional, deferred to a future lab machine.**
  Nothing in the current plans assumes GPU availability; everything is
  scoped to run (even if slowly, for the fine-tuning case) on this
  machine's CPU-only, 8 GB environment.
- **Reproducibility over raw speed.** Every plan in this document fixes
  and records its random seed(s) and configuration, per
  [`RESEARCH_LIMITATIONS.md`](RESEARCH_LIMITATIONS.md) and the pattern
  already established in `ml/stance_classification/dataset_prep.py`'s
  manifest.

## Bottom line

This machine can run every planned experiment **except** full transformer
fine-tuning at a comfortable pace — and even that is possible, just slow
and not recommended as a first choice given the realistic dataset size
from a single-annotator pilot batch. The TF-IDF baselines and the SBERT
embedding + classifier path are the right starting point precisely because
they're both fast here and (per
`STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md`) not obviously worse at this
dataset size — "do not assume the most complex model is the best model"
is not just a constraint to satisfy, it's the actual expectation given
what a few hundred labeled examples can support.

# Semantic Grouping (Concern/Topic Clustering) — Experiment Plan

**Status:** planning document only. No clustering has been run, no model
downloaded, no output produced. Hardware feasibility is assessed in
[`HARDWARE_FEASIBILITY_REPORT.md`](HARDWARE_FEASIBILITY_REPORT.md).

## Relationship to stance classification: deliberately independent

**Semantic grouping answers a different question than stance
classification, and this plan keeps the two independent by design:**

- Stance classification asks: *is this comment for or against the policy?*
- Semantic grouping asks: *which comments are raising the same underlying
  concern or idea, regardless of their stance on it?*

Two comments can land in the same concern group while disagreeing with
each other — e.g. "the fee increase is too high" (Oppose) and "the fee
increase is reasonable given inflation" (Support) are plausibly the *same
concern* (the fee increase) from opposite stances. Grouping must not
collapse onto stance as a side effect, so:

- Clustering in this plan runs on **all eligible comments' text embeddings**,
  never on stance labels, never using stance as a feature, and never
  stratified or split by stance before clustering.
- **Cluster output is never treated as a stance label**, and in particular
  **K-Means or HDBSCAN cluster assignments are never used as ground-truth
  stance** for any comment, under any circumstance. A cluster is a concern
  grouping, full stop — if someone wants a per-cluster stance breakdown
  later, that's computed by joining a cluster assignment against the
  *separately, humanly annotated* stance label for each comment in it, not
  by inferring stance from cluster membership.
- Evaluating "does this concern group contain a mix of stances" is a
  legitimate, useful **analysis of the clustering's output** once both
  clustering and stance labels exist — it is not a step in producing
  either one.

## Pipeline

```
eligible comment text (not excluded, per D8)
    -> sentence embeddings (same SBERT model family as classification Experiment 3,
       for consistency and to reuse the embedding cache in ml/embeddings/)
    -> dimensionality reduction (UMAP), where justified -- see below
    -> clustering (HDBSCAN primary, K-Means as a comparison run)
    -> noise/outlier handling
    -> cluster quality evaluation
    -> representative comment selection per cluster
    -> cluster-level summary (non-generative, extractive approach; see caveat below)
```

### Sentence embeddings

Same model choice as `STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md` Experiment
3 (`sentence-transformers/all-MiniLM-L6-v2` or a multilingual variant if
French comments are included) — not because the two pipelines are coupled,
but so the same cached embedding matrix (`ml/embeddings/`) can serve both,
rather than computing and holding two different embedding sets in memory
at once (per the hardware-respecting practices in
`HARDWARE_FEASIBILITY_REPORT.md`).

### Dimensionality reduction (UMAP) — "where justified"

- **Justified when:** the embedding dimensionality (384 for MiniLM) is high
  relative to the number of comments being clustered, and/or HDBSCAN's
  density-based assumptions behave better in a lower-dimensional space.
  UMAP to a modest target (e.g. 10–50 dimensions for clustering, 2 for
  visualization only) is the standard, well-justified choice here.
- **Not justified / skip when:** the comment count for a given
  policy/run is small enough (low hundreds) that UMAP's own
  hyperparameters (`n_neighbors`, `min_dist`) become unstable or
  arbitrary at that scale — in that regime, try clustering directly on
  the full-dimensional embeddings first and only add UMAP if it
  demonstrably improves cluster separation (evaluated per the quality
  metrics below), not by default.
- UMAP is stochastic unless seeded — **always fix `random_state`** for
  reproducibility, recorded alongside the rest of the run's configuration.

### Clustering: HDBSCAN (primary) vs. K-Means (comparison)

| | HDBSCAN | K-Means |
|---|---|---|
| **Role in this plan** | Primary method | Comparative experiment |
| **Why** | Does not require specifying the number of concerns in advance (unknown and probably not fixed across policies); naturally produces a noise/outlier category for comments that don't cleanly belong to any concern group, which matches the reality that public comment corpora contain a long tail of idiosyncratic or off-topic-but-not-excluded content. | A standard, well-understood baseline for comparison — forces a chosen *k*, which is itself informative to report (e.g. "HDBSCAN found ~12 natural clusters; does a forced K-Means at k=12 produce similar or different groupings?"). |
| **Noise handling** | Native (`label == -1`) — see below. | None natively; every point is assigned to some cluster even if it's a poor fit, which is itself a point of comparison against HDBSCAN's explicit noise category. |
| **Key hyperparameters to record** | `min_cluster_size`, `min_samples`, metric | `k`, `n_init`, `random_state` |

K-Means is run **as a comparison, not a replacement** — the plan's primary
deliverable (representative comments, summaries) is built from the
HDBSCAN run, with K-Means reported alongside as a sanity check on cluster
count and stability, not as an alternative final output to pick between
based on looks alone.

### Noise and outlier handling

- HDBSCAN's `-1` ("noise") label is **reported, not discarded** — noise
  comments are still real public comments and remain in every downstream
  dataset; they are simply not assigned to a concern group. Report the
  noise fraction explicitly (if it's large, that's a signal about either
  the embedding/parameter choice or genuine topic diversity, not
  necessarily a clustering failure).
- Comments excluded from stance labeling (rule D8: SPAM, OFF_TOPIC,
  TOO_SHORT_NONSUBSTANTIVE, UNINTELLIGIBLE) are **excluded from clustering
  input entirely**, upstream of HDBSCAN/K-Means — a spam comment has no
  concern to group, and forcing it into a cluster (or even into the noise
  bucket as if it were a meaningful near-miss) would misrepresent what the
  noise category means. This mirrors the stance-classification pipeline's
  own `separate_labels_and_exclusions` step in
  `ml/stance_classification/dataset_prep.py` — same principle, applied to
  a different pipeline.

### Cluster quality evaluation

- **Silhouette score** (on the embeddings actually clustered on, i.e.
  post-UMAP if UMAP was used) — standard, but known to be a weaker signal
  for HDBSCAN's variable-density clusters than for K-Means' spherical
  assumption; report it for both methods for comparability, with that
  caveat stated alongside the number, not silently.
- **HDBSCAN's own relative validity index** (`hdbscan.validity.validity_index`),
  which is designed for exactly this clustering method's density
  assumptions and is the more trustworthy metric for the primary
  (HDBSCAN) run.
- **Cluster size distribution** (are concerns roughly evenly sized, or is
  it a few large clusters plus many small ones? both are plausible and
  real for public comment data).
- **Qualitative spot-check:** for a sample of clusters, read several member
  comments directly and confirm they plausibly share a concern — an
  automatic metric is not a substitute for this, especially at pilot
  scale.

### Representative comment selection

Per cluster, select the comment(s) whose embedding is closest (cosine
similarity) to the cluster's centroid (K-Means) or to its densest region
(HDBSCAN — e.g. the medoid of the cluster's core points). Select a small,
fixed number (e.g. 3–5) per cluster, not just one, so a human reviewer
sees some of the cluster's internal variation, not a single cherry-picked
example.

### Cluster-level summaries — extractive first, generative flagged as future work

This plan defaults to an **extractive** summary approach for the initial
pass: the representative comments selected above, presented as-is (not
rewritten), optionally alongside simple descriptive stats (cluster size,
stance-label breakdown once available, example source metadata). This
keeps the summary traceable directly back to real comment text with no
generation step to validate.

A generative, abstractive summary (an actual one- or two-sentence
synthesized description of the concern) is a reasonable future step, but
is **out of scope for this plan** as written — it would introduce a new
category of validation need (does the generated summary accurately
represent the cluster? is it ever misleading or hallucinated?) that
deserves its own explicit scoping, not an implicit add-on here.

## Reproducibility

Every clustering run records: embedding model name/version, UMAP
hyperparameters (or explicit note that UMAP was skipped and why),
HDBSCAN/K-Means hyperparameters, random seed(s), input comment count and
exclusion count, and the resulting cluster count/size distribution/noise
fraction — mirroring the manifest pattern already established in
`ml/stance_classification/dataset_prep.py`'s `split_manifest.json`.

## Expected limitations

- At pilot scale (the current single-annotator batch is only 250 items,
  and even the full eligible corpus is ~7,941 English-language comments
  per `SINGLE_ANNOTATOR_PROTOCOL.md` section 4.1), cluster counts and
  shapes are likely to be unstable across minor hyperparameter changes —
  report this instability explicitly (e.g. by re-running with 2–3 seeds)
  rather than presenting one run's output as definitive.
- Concern clusters are about **topic**, not sentiment — a cluster mixing
  Support and Oppose comments on the same concern is an expected, correct
  outcome, not a clustering error, per the independence principle at the
  top of this document.
- HDBSCAN's noise fraction and silhouette/validity scores are diagnostic,
  not pass/fail gates — there is no single number this plan treats as
  "good enough to ship"; cluster quality here is judged by a combination
  of the quantitative metrics and the qualitative spot-check.

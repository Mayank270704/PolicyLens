# Repeat Annotation Procedure (Intra-Annotator Reliability)

Implements `SINGLE_ANNOTATOR_PROTOCOL.md` section 7 via
`scripts/annotation/repeat.py`. This procedure measures how consistently
the **same person** labels the **same comments** roughly two weeks apart.
It is **intra-annotator (test-retest) reliability**. It is **not**, and
must never be reported as, inter-annotator agreement — there is exactly
one human annotator in this experiment.

## The hidden repeat subset

38 of the 250 `comment_id`s in `annotation_batch_001.csv` (15.2%) were
designated as the repeat subset when the batch was generated, listed in
`data/annotations/new_experiment/repeat_annotation_plan.json`
(`repeat_subset_comment_ids`). They were drawn uniformly at random
(`random.Random(42)`, without replacement) from the finalized 250-item
sample, **after** stratified selection was locked in, so the repeat draw
doesn't bias which strata get re-checked.

During the first pass, these 38 items are annotated exactly like any other
item in `annotation_batch_001.csv` — the GUI never reads
`repeat_annotation_plan.json` and gives no visual indication that an item
is part of the repeat subset. The annotator is not meant to know which
items these are while doing the first pass.

## Step 1 — complete the first pass

Annotate all 250 items in `annotation_batch_001.csv` via
`python scripts/annotation/gui.py` as normal. The moment the 250th item
gets a label or exclusion code, the app records a completion timestamp
automatically (visible via `repeat.py status`, below).

## Step 2 — wait for the 14-day gate

```
python scripts/annotation/repeat.py status
```

Reports whether the gate is open yet, and how many days remain if not.
There is **no bypass flag** — `repeat.py prepare` (step 3) will refuse to
run until at least `schema.MIN_REPEAT_GAP_DAYS` (14) calendar days have
passed since the first-pass completion timestamp. This gap exists so the
second pass reflects genuine re-judgment rather than memory of the exact
label just assigned.

## Step 3 — generate the blind second-pass batch

Once the gate is open:

```
python scripts/annotation/repeat.py prepare
```

This writes `data/annotations/new_experiment/repeat_pass_batch.csv`: the
same 38 comments, with `comment_text`/`policy_context`/`policy_section`
copied fresh from the first-pass file, but **all four label fields reset
to blank** — the first-pass labels are never written into this file, so
there's no way to see them while doing the second pass. Row order is
reshuffled with a seed (`7`) distinct from every other seed used in this
project, so the file's order carries no information either.

`prepare` refuses to run (and writes nothing) if:
- the main batch isn't 100% complete yet, or
- the 14-day gate hasn't opened yet, or
- `repeat_pass_batch.csv` already exists (to avoid clobbering an
  in-progress second pass — this is a deliberate, un-overridable safety
  check in the CLI).

**Blinding in practice:** per the protocol, treat this file as an ordinary
new mini-batch rather than an obviously-labeled "consistency check" —
annotate it in the normal course of work (e.g., interleaved with the start
of a later batch) rather than specifically remembering "this is the repeat
test."

## Step 4 — annotate the second pass

```
python scripts/annotation/gui.py --batch data/annotations/new_experiment/repeat_pass_batch.csv
```

Same interface, same rules, same requirement that `Unclear` labels carry
notes. This file gets its own resume pointer and its own
`original_backup.csv`, independent of the main batch.

## Step 5 — compute the consistency report

Once all 38 items in `repeat_pass_batch.csv` have a label or exclusion
code:

```
python scripts/annotation/repeat.py kappa
```

This **refuses to compute anything, and fabricates no data**, if either
pass is incomplete — it will tell you exactly which `comment_id`s are
still pending. Once both passes are complete, it writes
`repeat_consistency_report.json` containing:

- **Exclusion agreement** — raw agreement rate on the binary
  excluded-vs-labeled decision across all 38 items, both passes.
- **Stance kappa** — Cohen's kappa over the items that received one of the
  four stance labels in **both** passes (items excluded in either pass are
  dropped from this calculation, not coerced into it):
  ```
  kappa = (p_o - p_e) / (1 - p_e)
  ```
  where `p_o` is observed agreement and `p_e` is chance agreement from the
  pooled marginal label frequencies of the two passes.
- **Confusion matrix** — a 4x4 count of (pass-1 label, pass-2 label) pairs.
- **Class-wise agreement** — for each stance label, the fraction of
  pass-1 items with that label that received the same label in pass 2.

### Interpreting kappa (Landis & Koch bands)

| kappa | Interpretation |
|---|---|
| < 0.00 | no agreement |
| 0.00 – 0.20 | slight |
| 0.21 – 0.40 | fair |
| 0.41 – 0.60 | moderate |
| 0.61 – 0.80 | substantial |
| 0.81 – 1.00 | almost perfect |

`SINGLE_ANNOTATOR_PROTOCOL.md` section 9 suggests (without presupposing)
"substantial" (kappa >= 0.61) as a reasonable bar before treating
`annotation_batch_001.csv` as more than a provisional pilot batch.

## What this procedure deliberately does not do

- It does not let you skip the 14-day wait.
- It does not let you compute kappa from a partially-completed second pass.
- It does not infer, interpolate, or guess any second-pass label — every
  value in `repeat_pass_batch.csv` is typed in by the human annotator, or
  the report simply isn't generated.

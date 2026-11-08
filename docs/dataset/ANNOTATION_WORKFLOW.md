# Single-Annotator Annotation Workflow

Implementation of the methodology in
[`SINGLE_ANNOTATOR_PROTOCOL.md`](SINGLE_ANNOTATOR_PROTOCOL.md). This document
covers the tooling under `scripts/annotation/` end to end: setup,
annotating, tracking progress, validating, the repeat-annotation reliability
check, and finalizing.

**This is a single-annotator experiment.** Every statistic this tooling can
produce about agreement is **intra-annotator (test-retest)**, never
inter-annotator agreement — there is one human annotator (the project
owner) throughout. Nothing in this tooling assigns, predicts, or suggests a
label; every `annotator_label` / `exclusion_code` / `annotation_confidence`
/ `annotation_notes` value is typed in by the annotator through
[the interface](ANNOTATION_INTERFACE_GUIDE.md).

## Components

| Module | Task | Purpose |
|---|---|---|
| `scripts/annotation/schema.py` | — | Shared constants (paths, label set, exclusion codes, confidence scale, length-tertile cut points) and small I/O helpers (atomic CSV write, SHA-256). |
| `scripts/annotation/state.py` | — | Per-batch resume pointer, first-pass completion timestamp (gates the repeat wait), append-only audit log for overwritten labels, one-time backup creation. |
| `scripts/annotation/setup.py` | — | One-time setup: creates the original blank-batch backup and a SHA-256 baseline for every file this experiment must never modify. |
| `scripts/annotation/validate.py` | 1 | Schema, ID, label, exclusion, confidence, and immutability validation. |
| `scripts/annotation/progress.py` | 2 | Progress report: counts, distributions, completion by stratum. |
| `scripts/annotation/gui.py` | 3 | Tkinter annotation interface. |
| `scripts/annotation/repeat.py` | 4 | Hidden repeat-subset preparation, 14-day gate enforcement, Cohen's kappa. |
| `scripts/annotation/finalize.py` | 5 | Completeness check, export, reproducibility report. |

## End-to-end sequence

```
1. python scripts/annotation/setup.py
     -> creates annotation_batch_001.original_backup.csv (if missing)
     -> creates protected_baseline.json (hashes of corpus + historical files)
     -> initializes annotation_state.json

2. python scripts/annotation/gui.py
     -> annotate all 250 items (see ANNOTATION_INTERFACE_GUIDE.md)
     -> progress persists automatically; safe to close and resume any time

3. python scripts/annotation/progress.py        (at any point, as often as you like)
4. python scripts/annotation/validate.py        (at any point)

     ... once all 250 rows are labeled or excluded, annotation_state.json
         records the completion timestamp automatically ...

5. Wait >= 14 days (see REPEAT_ANNOTATION_PROCEDURE.md)
6. python scripts/annotation/repeat.py status    (confirms the gate is open)
7. python scripts/annotation/repeat.py prepare   (writes repeat_pass_batch.csv)
8. python scripts/annotation/gui.py --batch data/annotations/new_experiment/repeat_pass_batch.csv
     -> annotate the 38 repeat items a second time
9. python scripts/annotation/repeat.py kappa     (writes repeat_consistency_report.json)

10. python scripts/annotation/finalize.py        (writes finalized/ export + reproducibility report)
```

Steps 3/4 can be run at any time during step 2 — they are read-only and
never block annotation.

## Design choices worth knowing

- **Everything is a flat CSV plus small JSON state files.** No database, no
  server, no network calls — matches the "no cloud APIs, CPU-only 8 GB
  laptop" constraint and keeps every artifact diffable and git-friendly.
- **All writes are atomic** (`schema.write_rows_atomic`: write to a `.tmp`
  file, then `os.replace`). A crash mid-save can never corrupt the batch
  CSV into a half-written state.
- **The original blank batch is backed up once, on first use, and never
  touched again.** `validate.py`'s immutability check compares every row's
  `comment_text` / `policy_context` / `policy_section` / `source_*` /
  `language` / `word_count` against that backup on every run.
- **Overwriting an existing label is allowed but tracked.** The GUI asks
  for confirmation and appends an entry to `audit_log.csv` (old value, new
  value, timestamp) rather than silently discarding the original call, per
  `STANCE_ANNOTATION_GUIDELINES.md` section 4 ("No label changes outside
  the documented workflow").
- **The repeat gate is a hard stop, not a warning.** `repeat.py prepare`
  raises an error and writes nothing if the main batch isn't 100% complete
  or fewer than 14 days have passed since it was. There is no bypass flag
  in the CLI.
- **Nothing here will fabricate a second annotation pass.**
  `repeat.compute_consistency_report` raises an error (and computes
  nothing) if either pass is incomplete, rather than filling gaps with any
  placeholder value.
- **`finalize.py` refuses to run on an incomplete batch** and never edits
  `annotation_batch_001.csv` — it only ever reads it and writes a separate
  export under `data/annotations/new_experiment/finalized/`.

## Related documentation

- [`SINGLE_ANNOTATOR_PROTOCOL.md`](SINGLE_ANNOTATOR_PROTOCOL.md) — the
  methodology and sampling design this tooling implements.
- [`ANNOTATION_INTERFACE_GUIDE.md`](ANNOTATION_INTERFACE_GUIDE.md) — how to
  use the GUI.
- [`DATA_VALIDATION.md`](DATA_VALIDATION.md) — every validation rule, what
  triggers it, and why.
- [`REPEAT_ANNOTATION_PROCEDURE.md`](REPEAT_ANNOTATION_PROCEDURE.md) — the
  14-day gate, blinding, and kappa methodology in full.
- [`EXPERIMENT_STATUS_REPORT.md`](EXPERIMENT_STATUS_REPORT.md) — current
  status snapshot of this experiment.
- `STANCE_LABEL_DEFINITIONS.md` / `STANCE_ANNOTATION_GUIDELINES.md` — the
  taxonomy and rules the annotator applies; this tooling enforces their
  structural requirements (valid labels, required notes, exclusion
  precedence) but cannot verify that a decision rule (D1–D8) was applied
  correctly — that remains a human judgment call.

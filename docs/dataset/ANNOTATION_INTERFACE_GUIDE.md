# Annotation Interface Guide

`scripts/annotation/gui.py` is a single-file Tkinter application (Python
standard library only — nothing new to install, no network access, fine on
a CPU-only 8 GB Windows laptop).

## Launching

```
python scripts/annotation/gui.py
```

This opens `data/annotations/new_experiment/annotation_batch_001.csv` by
default. To annotate a different file (for example, the second-pass repeat
batch once it exists):

```
python scripts/annotation/gui.py --batch data/annotations/new_experiment/repeat_pass_batch.csv
```

On first launch for any given batch file, the app creates a sibling
`<name>.original_backup.csv` — a frozen copy of the file in its pristine,
all-blank state. This backup is never overwritten; it is what
`validate.py` and `finalize.py` compare against to confirm comment text and
metadata were never altered.

## Layout

- **Top bar:** position within the current filter, overall completion
  count/percentage, and a filter dropdown (`All` / `Pending` / `Completed`
  / `Excluded`).
- **Context panel:** the stable `comment_id`, source dataset, language,
  word count, and the comment's `policy_context` / `policy_section` (see
  `SINGLE_ANNOTATOR_PROTOCOL.md` section 5 for what these contain and why).
- **Comment text:** read-only, full text, never truncated.
- **Stance label:** the four radio buttons — Support / Oppose / Neutral /
  Unclear.
- **Exclusion code:** SPAM / OFF_TOPIC / TOO_SHORT_NONSUBSTANTIVE /
  UNINTELLIGIBLE. Selecting one of these automatically clears any selected
  stance label, and vice versa — the two are mutually exclusive by
  construction, matching rule D8 (exclusion precedence).
- **Confidence:** Low (1) / Medium (2) / High (3) — see
  `SINGLE_ANNOTATOR_PROTOCOL.md` section 6.2 for the intended meaning of
  each level.
- **Notes:** free text. **Required before saving an Unclear label** — the
  app will block the save and explain why if notes are empty.
- **Previous / Next / Save / Save & Next** buttons.

## Navigation and resuming

- `Previous` / `Next` move within whatever filter is currently selected.
- Switching the filter jumps to the first item in the new filter; your
  position is remembered per filter pass.
- The app persists the index of the last item you viewed (in
  `annotation_state.json`, keyed by batch filename) every time you move or
  save. **Closing the app and reopening it later resumes exactly where you
  left off** — you do not need to find your place manually.

## Saving, overwriting, and unsaved changes

- `Save` and `Save & Next` write immediately to the CSV (atomically — a
  crash mid-write cannot corrupt the file).
- If you try to move to another item, switch filters, or close the window
  while the current item has unsaved changes, you'll be asked: **save**,
  **discard**, or **cancel and stay**. You can never silently lose an
  in-progress edit by navigating away.
- If you change the label/exclusion/confidence/notes on an item that
  **already had** a label or exclusion code recorded, saving will ask you
  to confirm the overwrite. If you confirm, the old and new values are
  appended to `data/annotations/new_experiment/audit_log.csv` with a
  timestamp — corrections are tracked, not silently discarded, per
  `STANCE_ANNOTATION_GUIDELINES.md` section 4.
- If a stance label is set but confidence is blank, saving will ask you to
  confirm — it's allowed, but you'll be nudged to fill it in.

## When the batch becomes 100% complete

The first time every row in the open batch has either a stance label or an
exclusion code, the app pops up a confirmation and records a completion
timestamp in `annotation_state.json`. For `annotation_batch_001.csv`, this
timestamp is what starts the mandatory 14-day wait before the hidden repeat
subset can be prepared — see
[`REPEAT_ANNOTATION_PROCEDURE.md`](REPEAT_ANNOTATION_PROCEDURE.md).

## Checking your work outside the GUI

```
python scripts/annotation/progress.py     # counts, distributions, completion by stratum
python scripts/annotation/validate.py     # structural correctness + immutability check
```

Both are read-only and safe to run at any time, including mid-session.

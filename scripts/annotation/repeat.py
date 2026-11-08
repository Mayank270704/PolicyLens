"""Task 4 — repeat-annotation (intra-annotator reliability) workflow.

Implements the design in repeat_annotation_plan.json and
docs/dataset/SINGLE_ANNOTATOR_PROTOCOL.md section 7:

- `prepare`: once the main batch is 100% complete AND at least
  MIN_REPEAT_GAP_DAYS have passed since that completion, generate a fresh,
  blank, reshuffled copy of the 38 repeat comment_ids (no first-pass labels
  attached) for a second annotation pass.
- `status`: report whether the gate is open yet, and how much of each pass
  is complete.
- `kappa`: once both passes are complete for all repeat ids, compute
  Cohen's kappa for intra-annotator stance consistency (never inter-
  annotator agreement), a separate exclusion-agreement rate, a confusion
  matrix, and class-wise agreement. Refuses to compute anything, and
  fabricates nothing, if either pass is incomplete.

Run directly:
    python scripts/annotation/repeat.py status
    python scripts/annotation/repeat.py prepare
    python scripts/annotation/repeat.py kappa
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.annotation import schema, state
else:
    from . import schema, state

EXCLUDED_SENTINEL = "__EXCLUDED__"
REPEAT_SHUFFLE_SEED = 7  # distinct from the batch-001 generation/selection seeds


def load_plan(plan_path: Path = schema.REPEAT_PLAN_PATH) -> dict:
    with open(plan_path, encoding="utf-8") as f:
        return json.load(f)


def days_remaining_in_gate(batch_path: Path = schema.MAIN_BATCH_PATH) -> float | None:
    """Returns days still remaining before the repeat gate opens, 0.0 (or
    negative) once open, or None if the main batch isn't complete yet."""
    completed_utc = state.get_completed_utc(batch_path)
    if not completed_utc:
        return None
    from datetime import datetime, timezone
    completed_at = schema.parse_iso(completed_utc)
    now = datetime.now(timezone.utc)
    elapsed_days = (now - completed_at).total_seconds() / 86400.0
    return schema.MIN_REPEAT_GAP_DAYS - elapsed_days


def gate_is_open(batch_path: Path = schema.MAIN_BATCH_PATH) -> tuple[bool, str]:
    remaining = days_remaining_in_gate(batch_path)
    if remaining is None:
        return False, "Main batch is not yet 100% annotated/excluded; the repeat gate has not started."
    if remaining > 0:
        return False, (
            f"Repeat gate not open yet: {remaining:.1f} of {schema.MIN_REPEAT_GAP_DAYS} "
            "required days remaining since first-pass completion."
        )
    return True, "Repeat gate is open."


def prepare_repeat_batch(
    main_batch_path: Path = schema.MAIN_BATCH_PATH,
    plan_path: Path = schema.REPEAT_PLAN_PATH,
    output_path: Path = schema.REPEAT_PASS_BATCH_PATH,
    allow_overwrite: bool = False,
) -> Path:
    """Build the blind second-pass batch for the hidden repeat subset.
    Refuses to run before the 14-day gate opens, and refuses to clobber an
    existing in-progress repeat-pass file unless explicitly told to."""
    is_open, reason = gate_is_open(main_batch_path)
    if not is_open:
        raise RuntimeError(reason)

    if output_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"{output_path} already exists. Refusing to overwrite a possibly in-progress "
            "repeat-pass file. Pass allow_overwrite=True only if you are certain it is safe."
        )

    plan = load_plan(plan_path)
    repeat_ids = set(plan["repeat_subset_comment_ids"])

    fieldnames, rows = schema.read_rows_with_fieldnames(main_batch_path)
    by_id = {r["comment_id"]: r for r in rows}
    missing = repeat_ids - set(by_id)
    if missing:
        raise RuntimeError(f"Repeat comment_ids missing from main batch: {sorted(missing)}")

    repeat_rows = []
    for cid in repeat_ids:
        src = by_id[cid]
        fresh = {col: src.get(col, "") for col in schema.IMMUTABLE_COLUMNS}
        fresh.update({
            "annotator_label": "",
            "exclusion_code": "",
            "annotation_confidence": "",
            "annotation_notes": "",
        })
        # reorder to the standard column order
        repeat_rows.append({col: fresh.get(col, "") for col in fieldnames})

    rng = random.Random(REPEAT_SHUFFLE_SEED)
    rng.shuffle(repeat_rows)

    schema.write_rows_atomic(output_path, repeat_rows, fieldnames)
    return output_path


def _label_or_exclusion(row: dict) -> tuple[str | None, bool]:
    """Returns (comparison_label, is_complete). comparison_label is the
    stance label, or EXCLUDED_SENTINEL if excluded; is_complete is False if
    neither a label nor an exclusion code is set."""
    label = (row.get("annotator_label") or "").strip()
    excl = (row.get("exclusion_code") or "").strip()
    if label:
        return label, True
    if excl:
        return EXCLUDED_SENTINEL, True
    return None, False


def check_passes_complete(
    main_batch_path: Path = schema.MAIN_BATCH_PATH,
    repeat_batch_path: Path = schema.REPEAT_PASS_BATCH_PATH,
    plan_path: Path = schema.REPEAT_PLAN_PATH,
) -> dict:
    plan = load_plan(plan_path)
    repeat_ids = set(plan["repeat_subset_comment_ids"])

    main_rows = {r["comment_id"]: r for r in schema.read_rows(main_batch_path)}
    pass1_incomplete = [cid for cid in repeat_ids if not _label_or_exclusion(main_rows.get(cid, {}))[1]]

    pass2_incomplete = list(repeat_ids)
    repeat_rows = {}
    if repeat_batch_path.exists():
        repeat_rows = {r["comment_id"]: r for r in schema.read_rows(repeat_batch_path)}
        pass2_incomplete = [cid for cid in repeat_ids if not _label_or_exclusion(repeat_rows.get(cid, {}))[1]]

    return {
        "repeat_subset_size": len(repeat_ids),
        "pass1_complete": len(pass1_incomplete) == 0,
        "pass1_incomplete_ids": sorted(pass1_incomplete),
        "pass2_file_exists": repeat_batch_path.exists(),
        "pass2_complete": repeat_batch_path.exists() and len(pass2_incomplete) == 0,
        "pass2_incomplete_ids": sorted(pass2_incomplete),
    }


def cohens_kappa(labels1: list[str], labels2: list[str], classes) -> float | None:
    n = len(labels1)
    if n == 0 or n != len(labels2):
        return None
    observed = sum(1 for a, b in zip(labels1, labels2) if a == b) / n
    marg1 = Counter(labels1)
    marg2 = Counter(labels2)
    expected = sum((marg1.get(c, 0) / n) * (marg2.get(c, 0) / n) for c in classes)
    if expected >= 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1 - expected)


def interpret_kappa(kappa: float | None) -> str:
    if kappa is None:
        return "undefined (no comparable items)"
    if kappa < 0:
        return "no agreement"
    if kappa <= 0.20:
        return "slight"
    if kappa <= 0.40:
        return "fair"
    if kappa <= 0.60:
        return "moderate"
    if kappa <= 0.80:
        return "substantial"
    return "almost perfect"


def compute_consistency_report(
    main_batch_path: Path = schema.MAIN_BATCH_PATH,
    repeat_batch_path: Path = schema.REPEAT_PASS_BATCH_PATH,
    plan_path: Path = schema.REPEAT_PLAN_PATH,
) -> dict:
    """Computes the full intra-annotator consistency report. Raises
    RuntimeError (fabricating nothing) if either pass is incomplete."""
    status = check_passes_complete(main_batch_path, repeat_batch_path, plan_path)
    if not status["pass1_complete"]:
        raise RuntimeError(
            f"First pass incomplete for {len(status['pass1_incomplete_ids'])} repeat item(s): "
            f"{status['pass1_incomplete_ids']}. Refusing to compute kappa on fabricated data."
        )
    if not status["pass2_complete"]:
        detail = (
            "repeat_pass_batch.csv does not exist yet (run `prepare` after the 14-day gate opens)"
            if not status["pass2_file_exists"]
            else f"incomplete for {len(status['pass2_incomplete_ids'])} item(s): {status['pass2_incomplete_ids']}"
        )
        raise RuntimeError(f"Second pass is not complete: {detail}. No second round was fabricated.")

    plan = load_plan(plan_path)
    repeat_ids = plan["repeat_subset_comment_ids"]

    main_rows = {r["comment_id"]: r for r in schema.read_rows(main_batch_path)}
    repeat_rows = {r["comment_id"]: r for r in schema.read_rows(repeat_batch_path)}

    pass1_vals = {cid: _label_or_exclusion(main_rows[cid])[0] for cid in repeat_ids}
    pass2_vals = {cid: _label_or_exclusion(repeat_rows[cid])[0] for cid in repeat_ids}

    # Exclusion agreement: binary excluded vs. labeled, over all repeat ids.
    excl_agree = sum(
        1 for cid in repeat_ids
        if (pass1_vals[cid] == EXCLUDED_SENTINEL) == (pass2_vals[cid] == EXCLUDED_SENTINEL)
    )
    exclusion_agreement_rate = round(excl_agree / len(repeat_ids), 4) if repeat_ids else None

    # Stance-only subset: items with a real stance label in BOTH passes.
    stance_ids = [
        cid for cid in repeat_ids
        if pass1_vals[cid] != EXCLUDED_SENTINEL and pass2_vals[cid] != EXCLUDED_SENTINEL
    ]
    labels1 = [pass1_vals[cid] for cid in stance_ids]
    labels2 = [pass2_vals[cid] for cid in stance_ids]

    kappa = cohens_kappa(labels1, labels2, schema.STANCE_LABELS)

    confusion = {a: {b: 0 for b in schema.STANCE_LABELS} for a in schema.STANCE_LABELS}
    for a, b in zip(labels1, labels2):
        confusion[a][b] += 1

    class_wise = {}
    for c in schema.STANCE_LABELS:
        row_total = sum(confusion[c].values())
        class_wise[c] = {
            "pass1_count": row_total,
            "agreement_rate": round(confusion[c][c] / row_total, 4) if row_total else None,
        }

    excluded_both_or_either = len(repeat_ids) - len(stance_ids)

    report = {
        "generated_utc": schema.utcnow_iso(),
        "repeat_subset_size": len(repeat_ids),
        "exclusion_agreement": {
            "description": "Raw agreement rate on the binary excluded/labeled decision, across all "
                           "repeat items, both passes.",
            "agreement_rate": exclusion_agreement_rate,
        },
        "stance_kappa": {
            "description": "Intra-annotator (test-retest) Cohen's kappa over items that received a "
                           "stance label in BOTH passes. This is NOT inter-annotator agreement -- "
                           "there is exactly one human annotator.",
            "n_items_compared": len(stance_ids),
            "n_items_excluded_from_kappa": excluded_both_or_either,
            "kappa": round(kappa, 4) if kappa is not None else None,
            "interpretation": interpret_kappa(kappa),
        },
        "confusion_matrix": confusion,
        "class_wise_agreement": class_wise,
    }
    if len(stance_ids) < 20:
        report["stance_kappa"]["low_sample_warning"] = (
            f"Only {len(stance_ids)} item(s) contribute to this kappa estimate -- below the "
            "conventional ~30-item floor for a stable point estimate (see "
            "SINGLE_ANNOTATOR_PROTOCOL.md section 4.2). Treat this number as indicative only, "
            "not as a precise or final reliability figure."
        )
    for c, info in class_wise.items():
        if 0 < info["pass1_count"] < 5:
            info["low_sample_warning"] = (
                f"Only {info['pass1_count']} '{c}' item(s) in the repeat subset -- this class's "
                "agreement rate is not statistically meaningful at this sample size."
            )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Repeat-annotation (intra-annotator) workflow.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Report gate status and pass completion.")
    p_prepare = sub.add_parser("prepare", help="Generate the blind second-pass batch.")
    p_prepare.add_argument("--allow-overwrite", action="store_true")
    sub.add_parser("kappa", help="Compute and save the intra-annotator consistency report.")

    args = parser.parse_args(argv)

    if args.command == "status":
        is_open, reason = gate_is_open()
        passes = check_passes_complete()
        print(f"Repeat gate open: {is_open}")
        print(f"  {reason}")
        print(json.dumps(passes, indent=2))
        return 0

    if args.command == "prepare":
        try:
            path = prepare_repeat_batch(allow_overwrite=args.allow_overwrite)
        except (RuntimeError, FileExistsError) as e:
            print(f"Cannot prepare repeat batch: {e}")
            return 1
        print(f"Wrote blind repeat-pass batch: {path}")
        return 0

    if args.command == "kappa":
        try:
            report = compute_consistency_report()
        except RuntimeError as e:
            print(f"Cannot compute consistency report: {e}")
            return 1
        schema.REPEAT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(schema.REPEAT_REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(json.dumps(report, indent=2))
        print(f"\nSaved to {schema.REPEAT_REPORT_PATH}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())

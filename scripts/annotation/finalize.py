"""Task 5 — final dataset validation and export.

Refuses to run while any comment in the main batch is still pending. On
success, writes a clean copy of the validated annotations to
data/annotations/new_experiment/finalized/stance_annotations_final.csv
(the source batch file is only ever read, never modified) plus a
reproducibility report recording configuration, timestamps, file hashes,
and the repeat-annotation consistency results if available.

Run directly:
    python scripts/annotation/finalize.py
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.annotation import repeat, schema, validate
else:
    from . import repeat, schema, validate


class FinalizationError(RuntimeError):
    pass


def _display_path(path: Path) -> str:
    """Repo-relative path when possible (for a readable, portable report),
    falling back to the raw path for fixtures/files outside the repo."""
    try:
        return str(path.relative_to(schema.REPO_ROOT))
    except ValueError:
        return str(path)


def run_finalize(
    batch_path: Path = schema.MAIN_BATCH_PATH,
    backup_path: Path = schema.MAIN_BATCH_BACKUP_PATH,
    plan_path: Path = schema.REPEAT_PLAN_PATH,
    repeat_batch_path: Path = schema.REPEAT_PASS_BATCH_PATH,
    output_csv_path: Path = schema.FINALIZED_CSV_PATH,
    report_path: Path = schema.REPRODUCIBILITY_REPORT_PATH,
) -> dict:
    fieldnames, rows = schema.read_rows_with_fieldnames(batch_path)

    if not backup_path.exists():
        raise FinalizationError(
            f"No original backup found at {backup_path}; cannot verify comment text/metadata "
            "were never altered. Refusing to finalize."
        )
    backup_rows = schema.read_rows(backup_path)

    issues = validate.validate_batch(
        rows, fieldnames=fieldnames, backup_rows=backup_rows, require_complete=True
    )
    errors = [i for i in issues if i.severity == "ERROR"]
    if errors:
        raise FinalizationError(
            "Validation failed; refusing to finalize an incomplete or inconsistent batch:\n"
            + "\n".join(str(i) for i in errors)
        )

    if len(rows) != len(backup_rows):
        raise FinalizationError(
            f"Row count mismatch: working file has {len(rows)} rows, original backup has "
            f"{len(backup_rows)}. The original 250-item sample must be fully accounted for."
        )

    stance_counter = Counter((r.get("annotator_label") or "").strip() for r in rows if r.get("annotator_label"))
    exclusion_counter = Counter((r.get("exclusion_code") or "").strip() for r in rows if r.get("exclusion_code"))

    # Separate the two record types for the report (the CSV itself already
    # keeps them in mutually exclusive columns on the same row).
    labeled_rows = [r for r in rows if (r.get("annotator_label") or "").strip()]
    excluded_rows = [r for r in rows if (r.get("exclusion_code") or "").strip()]

    # Repeat/intra-annotator consistency, if available -- never fabricated.
    repeat_status = repeat.check_passes_complete(batch_path, repeat_batch_path, plan_path) if plan_path.exists() else None
    consistency_report = None
    if repeat_status and repeat_status["pass1_complete"] and repeat_status["pass2_complete"]:
        consistency_report = repeat.compute_consistency_report(batch_path, repeat_batch_path, plan_path)

    schema.write_rows_atomic(output_csv_path, rows, fieldnames)

    file_hashes = {
        "canonical_corpus_unique_texts": {
            "path": _display_path(schema.CORPUS_PATH),
            "sha256": schema.sha256_file(schema.CORPUS_PATH) if schema.CORPUS_PATH.exists() else None,
        },
        "annotation_batch_001_working": {
            "path": _display_path(batch_path),
            "sha256": schema.sha256_file(batch_path),
        },
        "annotation_batch_001_original_backup": {
            "path": _display_path(backup_path),
            "sha256": schema.sha256_file(backup_path),
        },
        "repeat_annotation_plan": {
            "path": _display_path(plan_path),
            "sha256": schema.sha256_file(plan_path) if plan_path.exists() else None,
        },
        "finalized_export": {
            "path": _display_path(output_csv_path),
            "sha256": schema.sha256_file(output_csv_path),
        },
    }
    if repeat_batch_path.exists():
        file_hashes["repeat_pass_batch"] = {
            "path": _display_path(repeat_batch_path),
            "sha256": schema.sha256_file(repeat_batch_path),
        }

    report = {
        "generated_utc": schema.utcnow_iso(),
        "protocol_reference": "docs/dataset/SINGLE_ANNOTATOR_PROTOCOL.md",
        "experiment_config": {
            "stance_labels": list(schema.STANCE_LABELS),
            "exclusion_codes": list(schema.EXCLUSION_CODES),
            "confidence_scale": schema.CONFIDENCE_LABELS,
            "length_tertile_cutpoints_words": {
                "short_max": schema.LENGTH_SHORT_MAX_WORDS,
                "medium_max": schema.LENGTH_MEDIUM_MAX_WORDS,
            },
            "min_repeat_gap_days": schema.MIN_REPEAT_GAP_DAYS,
            "repeat_subset_fraction_target": schema.REPEAT_SUBSET_FRACTION,
        },
        "row_count": len(rows),
        "labeled_count": len(labeled_rows),
        "excluded_count": len(excluded_rows),
        "stance_distribution": dict(sorted(stance_counter.items())),
        "exclusion_distribution": dict(sorted(exclusion_counter.items())),
        "validation": {
            "errors": 0,
            "warnings": len([i for i in issues if i.severity == "WARNING"]),
            "warning_detail": [str(i) for i in issues if i.severity == "WARNING"],
        },
        "intra_annotator_consistency": consistency_report if consistency_report else {
            "status": "not_available",
            "detail": (
                "Repeat subset second pass is not complete; no intra-annotator kappa computed. "
                "This dataset is PROVISIONAL and must not be described as validated or "
                "gold-standard until that check is run (see SINGLE_ANNOTATOR_PROTOCOL.md section 9)."
            ),
        },
        "file_hashes": file_hashes,
        "gold_standard_claim": "NOT MADE. This is a single-annotator provisional batch. See "
                                "SINGLE_ANNOTATOR_PROTOCOL.md section 9 for the conditions required "
                                "before any such claim.",
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Finalize and export completed stance annotations.")
    parser.add_argument("--batch", type=Path, default=schema.MAIN_BATCH_PATH)
    parser.add_argument("--backup", type=Path, default=schema.MAIN_BATCH_BACKUP_PATH)
    args = parser.parse_args(argv)

    try:
        report = run_finalize(batch_path=args.batch, backup_path=args.backup)
    except FinalizationError as e:
        print(f"FINALIZATION REFUSED:\n{e}")
        return 1

    print(f"Finalized {report['row_count']} rows "
          f"({report['labeled_count']} labeled, {report['excluded_count']} excluded).")
    print(f"Export: {schema.FINALIZED_CSV_PATH}")
    print(f"Reproducibility report: {schema.REPRODUCIBILITY_REPORT_PATH}")
    if report["intra_annotator_consistency"].get("status") == "not_available":
        print("\nNote: intra-annotator consistency (kappa) not yet available -- "
              "dataset remains PROVISIONAL.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

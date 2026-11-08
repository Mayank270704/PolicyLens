"""Task 1 — annotation data validation.

Checks a batch CSV for schema correctness, label/exclusion validity,
mutual exclusivity between stance labels and exclusion codes, confidence
scale compliance, duplicate/missing IDs, and (when a backup is supplied)
that no comment text or source metadata was altered by annotation.

This module never assigns a label. It only reports problems.

Run directly:
    python scripts/annotation/validate.py --batch data/annotations/new_experiment/annotation_batch_001.csv
    python scripts/annotation/validate.py --require-complete   # for pre-finalization checks
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.annotation import schema
else:
    from . import schema


@dataclass
class Issue:
    severity: str  # "ERROR" or "WARNING"
    code: str
    comment_id: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.code} ({self.comment_id}): {self.message}"


def validate_schema_columns(fieldnames) -> list[Issue]:
    fieldnames = fieldnames or []
    missing = [c for c in schema.REQUIRED_COLUMNS if c not in fieldnames]
    if missing:
        return [Issue("ERROR", "MISSING_COLUMNS", "-", f"Missing required columns: {missing}")]
    return []


def validate_ids(rows: list[dict]) -> list[Issue]:
    issues: list[Issue] = []
    seen: dict[str, int] = {}
    for i, row in enumerate(rows):
        cid = (row.get("comment_id") or "").strip()
        if not cid:
            issues.append(Issue("ERROR", "MISSING_ID", f"<row {i}>", "comment_id is blank"))
            continue
        if not cid.startswith(schema.COMMENT_ID_PREFIX):
            issues.append(
                Issue("WARNING", "ID_FORMAT", cid,
                      f"comment_id does not start with '{schema.COMMENT_ID_PREFIX}'")
            )
        if cid in seen:
            issues.append(
                Issue("ERROR", "DUPLICATE_ID", cid,
                      f"Duplicate comment_id (first seen at row {seen[cid]}, again at row {i})")
            )
        else:
            seen[cid] = i
    return issues


def validate_word_count_type(rows: list[dict]) -> list[Issue]:
    issues: list[Issue] = []
    for row in rows:
        cid = row.get("comment_id", "<unknown>")
        wc = row.get("word_count", "")
        try:
            int(wc)
        except (TypeError, ValueError):
            issues.append(Issue("ERROR", "INVALID_WORD_COUNT", cid, f"word_count '{wc}' is not an integer"))
    return issues


def validate_labels_and_exclusions(rows: list[dict]) -> list[Issue]:
    issues: list[Issue] = []
    for row in rows:
        cid = row.get("comment_id", "<unknown>")
        label = (row.get("annotator_label") or "").strip()
        excl = (row.get("exclusion_code") or "").strip()

        if label and label not in schema.STANCE_LABELS:
            issues.append(
                Issue("ERROR", "INVALID_LABEL", cid,
                      f"annotator_label '{label}' is not one of {list(schema.STANCE_LABELS)}")
            )
        if excl and excl not in schema.EXCLUSION_CODES:
            issues.append(
                Issue("ERROR", "INVALID_EXCLUSION_CODE", cid,
                      f"exclusion_code '{excl}' is not one of {list(schema.EXCLUSION_CODES)}")
            )
        if label and excl:
            issues.append(
                Issue("ERROR", "LABEL_AND_EXCLUSION_SET", cid,
                      "Both annotator_label and exclusion_code are set; a comment must be either "
                      "labeled or excluded, never both (rule D8)")
            )
    return issues


def validate_confidence(rows: list[dict]) -> list[Issue]:
    issues: list[Issue] = []
    for row in rows:
        cid = row.get("comment_id", "<unknown>")
        label = (row.get("annotator_label") or "").strip()
        conf = (row.get("annotation_confidence") or "").strip()
        if conf and conf not in schema.CONFIDENCE_VALUES:
            issues.append(
                Issue("ERROR", "INVALID_CONFIDENCE", cid,
                      f"annotation_confidence '{conf}' is not one of {list(schema.CONFIDENCE_VALUES)}")
            )
        if label and not conf:
            issues.append(
                Issue("WARNING", "MISSING_CONFIDENCE", cid,
                      "annotator_label is set but annotation_confidence is blank")
            )
    return issues


def validate_notes_requirements(rows: list[dict]) -> list[Issue]:
    issues: list[Issue] = []
    for row in rows:
        cid = row.get("comment_id", "<unknown>")
        label = (row.get("annotator_label") or "").strip()
        notes = (row.get("annotation_notes") or "").strip()
        if label == "Unclear" and not notes:
            issues.append(
                Issue("ERROR", "MISSING_REQUIRED_NOTES", cid,
                      "annotation_notes is required for every Unclear label "
                      "(STANCE_ANNOTATION_GUIDELINES.md section 3, step 9)")
            )
        if label == "Oppose" and not notes:
            issues.append(
                Issue("WARNING", "NOTES_RECOMMENDED", cid,
                      "annotation_notes is blank for an Oppose label; required if this was reached "
                      "via rule D4 (implementation-vs-substance) -- this cannot be checked "
                      "automatically, please confirm manually")
            )
    return issues


def validate_pending_vs_excluded(rows: list[dict], require_complete: bool) -> list[Issue]:
    issues: list[Issue] = []
    if not require_complete:
        return issues
    for row in rows:
        cid = row.get("comment_id", "<unknown>")
        label = (row.get("annotator_label") or "").strip()
        excl = (row.get("exclusion_code") or "").strip()
        if not label and not excl:
            issues.append(
                Issue("ERROR", "INCOMPLETE", cid,
                      "Comment has neither a stance label nor an exclusion code (still pending)")
            )
    return issues


def validate_immutable_fields(rows: list[dict], backup_rows: list[dict]) -> list[Issue]:
    issues: list[Issue] = []
    backup_by_id = {r["comment_id"]: r for r in backup_rows if r.get("comment_id")}
    working_ids = set()

    for row in rows:
        cid = row.get("comment_id", "<unknown>")
        working_ids.add(cid)
        backup = backup_by_id.get(cid)
        if backup is None:
            issues.append(
                Issue("ERROR", "ID_NOT_IN_BACKUP", cid,
                      "comment_id present in the working file but not in the original backup "
                      "(possible unauthorized insertion)")
            )
            continue
        for col in schema.IMMUTABLE_COLUMNS:
            if (row.get(col, "") or "") != (backup.get(col, "") or ""):
                issues.append(
                    Issue("ERROR", "IMMUTABLE_FIELD_CHANGED", cid,
                          f"Column '{col}' differs from the original backup; comment text and "
                          "source metadata must never be edited by annotation")
                )

    for cid in backup_by_id:
        if cid not in working_ids:
            issues.append(
                Issue("ERROR", "ID_MISSING_FROM_BATCH", cid,
                      "comment_id present in the original backup but missing from the working file")
            )
    return issues


def validate_batch(
    rows: list[dict],
    fieldnames: list[str] | None = None,
    backup_rows: list[dict] | None = None,
    require_complete: bool = False,
) -> list[Issue]:
    issues: list[Issue] = []
    if fieldnames is not None:
        issues += validate_schema_columns(fieldnames)
    issues += validate_ids(rows)
    issues += validate_word_count_type(rows)
    issues += validate_labels_and_exclusions(rows)
    issues += validate_confidence(rows)
    issues += validate_notes_requirements(rows)
    issues += validate_pending_vs_excluded(rows, require_complete=require_complete)
    if backup_rows is not None:
        issues += validate_immutable_fields(rows, backup_rows)
    return issues


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate a stance annotation batch CSV.")
    parser.add_argument("--batch", type=Path, default=schema.MAIN_BATCH_PATH)
    parser.add_argument("--backup", type=Path, default=schema.MAIN_BATCH_BACKUP_PATH)
    parser.add_argument(
        "--require-complete", action="store_true",
        help="Treat any pending (unlabeled, unexcluded) row as an error (used before finalization).",
    )
    parser.add_argument("--no-backup-check", action="store_true", help="Skip the immutability check.")
    args = parser.parse_args(argv)

    fieldnames, rows = schema.read_rows_with_fieldnames(args.batch)

    backup_rows = None
    if not args.no_backup_check and args.backup.exists():
        backup_rows = schema.read_rows(args.backup)

    issues = validate_batch(
        rows, fieldnames=fieldnames, backup_rows=backup_rows, require_complete=args.require_complete
    )

    errors = [i for i in issues if i.severity == "ERROR"]
    warnings = [i for i in issues if i.severity == "WARNING"]

    for issue in issues:
        print(issue)

    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s), {len(rows)} rows checked.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

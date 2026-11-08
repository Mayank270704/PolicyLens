"""Shared experiment-state and audit-log helpers.

`annotation_state.json` tracks, per batch file (keyed by filename): the
GUI's last-visited row index (for resume) and the UTC timestamp at which
that batch first became fully complete (every row labeled or excluded) --
the latter is what gates the 14-day repeat-annotation wait in repeat.py.

`audit_log.csv` is an append-only record of every overwrite of a
previously-set label, so corrections are tracked rather than silently
discarded, per STANCE_ANNOTATION_GUIDELINES.md section 4 ("No label
changes outside the documented workflow").
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.annotation import schema
else:
    from . import schema

AUDIT_FIELDNAMES = [
    "timestamp_utc",
    "batch_file",
    "comment_id",
    "old_annotator_label",
    "old_exclusion_code",
    "new_annotator_label",
    "new_exclusion_code",
]


def load_state() -> dict:
    if not schema.STATE_PATH.exists():
        return {"batches": {}}
    with open(schema.STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    schema.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = schema.STATE_PATH.with_name(schema.STATE_PATH.name + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    tmp_path.replace(schema.STATE_PATH)


def _batch_key(batch_path: Path) -> str:
    return Path(batch_path).name


def get_batch_state(state: dict, batch_path: Path) -> dict:
    return state.setdefault("batches", {}).setdefault(
        _batch_key(batch_path), {"last_index": 0, "completed_utc": None}
    )


def set_last_index(batch_path: Path, index: int) -> None:
    state = load_state()
    entry = get_batch_state(state, batch_path)
    entry["last_index"] = index
    save_state(state)


def get_last_index(batch_path: Path) -> int:
    state = load_state()
    entry = get_batch_state(state, batch_path)
    return int(entry.get("last_index", 0) or 0)


def mark_complete_if_needed(batch_path: Path, rows: list[dict]) -> bool:
    """If every row is labeled or excluded and no completion timestamp is
    recorded yet, record one now. Returns True if this call just completed it."""
    all_done = all(
        (row.get("annotator_label") or "").strip() or (row.get("exclusion_code") or "").strip()
        for row in rows
    )
    if not all_done:
        return False
    state = load_state()
    entry = get_batch_state(state, batch_path)
    if entry.get("completed_utc"):
        return False
    entry["completed_utc"] = schema.utcnow_iso()
    save_state(state)
    return True


def get_completed_utc(batch_path: Path) -> str | None:
    state = load_state()
    entry = get_batch_state(state, batch_path)
    return entry.get("completed_utc")


def append_audit_entry(
    batch_path: Path,
    comment_id: str,
    old_label: str,
    old_excl: str,
    new_label: str,
    new_excl: str,
) -> None:
    schema.AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    is_new = not schema.AUDIT_LOG_PATH.exists()
    with open(schema.AUDIT_LOG_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_FIELDNAMES)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "timestamp_utc": schema.utcnow_iso(),
            "batch_file": _batch_key(batch_path),
            "comment_id": comment_id,
            "old_annotator_label": old_label,
            "old_exclusion_code": old_excl,
            "new_annotator_label": new_label,
            "new_exclusion_code": new_excl,
        })


TIMING_FIELDNAMES = ["timestamp_utc", "batch_file", "comment_id", "action"]


def append_timing_event(batch_path: Path, comment_id: str, action: str = "saved") -> None:
    """Append-only log of every save event, used only as an approximate
    signal for annotation-time analysis (scripts/annotation/timing.py) --
    never for anything that affects the label data itself."""
    schema.TIMING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    is_new = not schema.TIMING_LOG_PATH.exists()
    with open(schema.TIMING_LOG_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TIMING_FIELDNAMES)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "timestamp_utc": schema.utcnow_iso(),
            "batch_file": _batch_key(batch_path),
            "comment_id": comment_id,
            "action": action,
        })


def ensure_backup(batch_path: Path, backup_path: Path) -> bool:
    """Copy batch_path to backup_path if backup_path does not already
    exist. Returns True if a backup was just created. Never overwrites an
    existing backup."""
    if backup_path.exists():
        return False
    fieldnames, rows = schema.read_rows_with_fieldnames(batch_path)
    schema.write_rows_atomic(backup_path, rows, fieldnames)
    return True

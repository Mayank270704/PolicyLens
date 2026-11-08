"""Shared constants and small I/O helpers for the single-annotator workflow.

Column set, label set, exclusion codes, confidence scale, and the length-
tertile cut points here must stay in sync with
docs/dataset/SINGLE_ANNOTATOR_PROTOCOL.md (sections 4.3 and 6) — that
document is the normative source; this module is its machine-readable
mirror.
"""
from __future__ import annotations

import csv
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = REPO_ROOT / "data"
CORPUS_PATH = DATA_DIR / "processed" / "canonical_corpus" / "unique_texts.csv"

HISTORICAL_DIR = DATA_DIR / "annotations" / "previous_research"
HISTORICAL_600_PATH = HISTORICAL_DIR / "consolidated_stance_dataset_corrected.csv"
HISTORICAL_400_PATH = HISTORICAL_DIR / "stance_human_gold_400_provisional.csv"
HISTORICAL_134_PATH = HISTORICAL_DIR / "targeted_annotation_200" / "stance_targeted_master.csv"
HISTORICAL_134_BLIND_PATH = HISTORICAL_DIR / "targeted_annotation_200" / "stance_targeted_reviewer_blind.csv"

EXPERIMENT_DIR = DATA_DIR / "annotations" / "new_experiment"
MAIN_BATCH_PATH = EXPERIMENT_DIR / "annotation_batch_001.csv"
MAIN_BATCH_BACKUP_PATH = EXPERIMENT_DIR / "annotation_batch_001.original_backup.csv"
REPEAT_PLAN_PATH = EXPERIMENT_DIR / "repeat_annotation_plan.json"
REPEAT_PASS_BATCH_PATH = EXPERIMENT_DIR / "repeat_pass_batch.csv"
REPEAT_PASS_BACKUP_PATH = EXPERIMENT_DIR / "repeat_pass_batch.original_backup.csv"
REPEAT_REPORT_PATH = EXPERIMENT_DIR / "repeat_consistency_report.json"
STATE_PATH = EXPERIMENT_DIR / "annotation_state.json"
AUDIT_LOG_PATH = EXPERIMENT_DIR / "audit_log.csv"
TIMING_LOG_PATH = EXPERIMENT_DIR / "annotation_events.csv"
PROTECTED_BASELINE_PATH = EXPERIMENT_DIR / "protected_baseline.json"
FINALIZED_DIR = EXPERIMENT_DIR / "finalized"
FINALIZED_CSV_PATH = FINALIZED_DIR / "stance_annotations_final.csv"
REPRODUCIBILITY_REPORT_PATH = FINALIZED_DIR / "reproducibility_report.json"

REQUIRED_COLUMNS = [
    "comment_id",
    "comment_text",
    "policy_context",
    "policy_section",
    "annotator_label",
    "exclusion_code",
    "annotation_confidence",
    "annotation_notes",
    "source_unique_id",
    "source_dataset",
    "language",
    "word_count",
]

# Columns that describe the comment itself (not the annotation of it).
# These must be byte-identical to the original blank backup forever.
IMMUTABLE_COLUMNS = [
    "comment_id",
    "comment_text",
    "policy_context",
    "policy_section",
    "source_unique_id",
    "source_dataset",
    "language",
    "word_count",
]

LABEL_COLUMNS = [
    "annotator_label",
    "exclusion_code",
    "annotation_confidence",
    "annotation_notes",
]

STANCE_LABELS = ("Support", "Oppose", "Neutral", "Unclear")
EXCLUSION_CODES = ("SPAM", "OFF_TOPIC", "TOO_SHORT_NONSUBSTANTIVE", "UNINTELLIGIBLE")

CONFIDENCE_VALUES = ("1", "2", "3")
CONFIDENCE_LABELS = {"1": "Low", "2": "Medium", "3": "High"}

# Length-tertile cut points on word count, computed over the eligible pool
# in SINGLE_ANNOTATOR_PROTOCOL.md section 4.3: short 1-9, medium 10-21, long 22+.
LENGTH_SHORT_MAX_WORDS = 9
LENGTH_MEDIUM_MAX_WORDS = 21

MIN_REPEAT_GAP_DAYS = 14
REPEAT_SUBSET_FRACTION = 0.15

COMMENT_ID_PREFIX = "PL-"


def length_bucket(word_count: int) -> str:
    if word_count <= LENGTH_SHORT_MAX_WORDS:
        return "short"
    if word_count <= LENGTH_MEDIUM_MAX_WORDS:
        return "medium"
    return "long"


def read_rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def read_rows_with_fieldnames(path: Path) -> tuple[list[str], list[dict]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        return fieldnames, list(reader)


def write_rows_atomic(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    """Write rows to path via a temp file + atomic rename, so a crash or
    power loss mid-write can never leave a half-written, corrupt CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")
    with open(tmp_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    os.replace(tmp_path, path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def is_blank(value) -> bool:
    return value is None or str(value).strip() == ""

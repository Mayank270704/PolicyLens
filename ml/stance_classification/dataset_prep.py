"""Phase C — ML dataset preparation architecture for stance classification.

Consumes the FINALIZED annotation export produced by
scripts/annotation/finalize.py
(data/annotations/new_experiment/finalized/stance_annotations_final.csv) --
never the raw working batch mid-annotation, and never any pseudo-labeled
or AI-predicted file. Builds reproducible, leakage-safe train/val/test
splits for a future model-training phase.

No model is trained here. This module only prepares data.

Run directly:
    python ml/stance_classification/dataset_prep.py
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.annotation import schema as ann_schema

REPO_ROOT = ann_schema.REPO_ROOT
DEFAULT_SOURCE_PATH = ann_schema.FINALIZED_CSV_PATH
DEFAULT_OUTPUT_DIR = ann_schema.DATA_DIR / "processed" / "stance_classification_splits"
DEFAULT_SPLIT_FRACTIONS = {"train": 0.7, "val": 0.15, "test": 0.15}
DEFAULT_SPLIT_SEED = 20261108

SPLIT_COLUMNS = ann_schema.REQUIRED_COLUMNS + ["normalized_text"]


class DatasetPrepError(RuntimeError):
    pass


def load_finalized_annotations(path: Path = DEFAULT_SOURCE_PATH) -> list[dict]:
    """Loads the finalized export. Raises clearly (does not fall back to
    the raw working batch, and never to any AI-labeled file) if it doesn't
    exist yet -- there is nothing to prepare until genuine human
    annotations have been finalized."""
    path = Path(path)
    if not path.exists():
        raise DatasetPrepError(
            f"No finalized annotation export found at {path}. This module only ever consumes "
            "scripts/annotation/finalize.py's output -- run the annotation workflow to "
            "completion first (see docs/dataset/ANNOTATION_WORKFLOW.md). Refusing to fall back "
            "to the raw working batch or to any AI-predicted labels."
        )
    return ann_schema.read_rows(path)


def normalize_text(text: str) -> str:
    """A modeling-only transform (whitespace collapse + trim). Always
    returned as a NEW value in a NEW column (`normalized_text`) -- the
    original `comment_text` column is never overwritten, per the
    source-text-is-immutable principle this whole project follows."""
    return re.sub(r"\s+", " ", text or "").strip()


def separate_labels_and_exclusions(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Returns (labeled_rows, excluded_rows). A row with neither (still
    pending) is dropped from both -- it should never reach this stage;
    finalize.py already refuses to export an incomplete batch."""
    labeled = [r for r in rows if (r.get("annotator_label") or "").strip()]
    excluded = [r for r in rows if (r.get("exclusion_code") or "").strip()]
    return labeled, excluded


def prepare_classification_rows(rows: list[dict]) -> list[dict]:
    """Labeled rows only (exclusions are not classification targets, per
    the protocol -- D8 excludes them from stance labeling entirely), each
    augmented with a `normalized_text` column."""
    labeled, _ = separate_labels_and_exclusions(rows)
    out = []
    for r in labeled:
        new_row = dict(r)
        new_row["normalized_text"] = normalize_text(r["comment_text"])
        out.append(new_row)
    return out


def _dedup_group_key(row: dict) -> str:
    """Case-insensitive, whitespace-collapsed text identity. Two comments
    that are exact duplicates (or differ only in whitespace/case) must
    never land in different splits -- that's train/test leakage."""
    return normalize_text(row["comment_text"]).lower()


def build_dedup_groups(rows: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[_dedup_group_key(row)].append(row)
    return groups


@dataclass
class SplitResult:
    train: list[dict]
    val: list[dict]
    test: list[dict]
    config: dict

    def as_dict(self) -> dict[str, list[dict]]:
        return {"train": self.train, "val": self.val, "test": self.test}


def make_splits(
    rows: list[dict],
    split_fractions: dict[str, float] | None = None,
    seed: int = DEFAULT_SPLIT_SEED,
    stratify_field: str = "annotator_label",
) -> SplitResult:
    """Group-aware, stratified, reproducible train/val/test split.

    - Operates on classification-eligible rows only (call
      prepare_classification_rows first) -- exclusions never enter a split.
    - Duplicate-text leakage prevention: rows are first grouped by
      normalized, case-folded text; a group is assigned to exactly one
      split as a unit, so no duplicate/near-duplicate comment can appear
      in both train and test.
    - Stratified by `stratify_field` (default: the stance label) at the
      GROUP level (a group's majority label decides its stratum), so each
      split's class balance tracks the overall distribution as closely as
      group-level assignment allows -- see SINGLE_ANNOTATOR_PROTOCOL.md
      section 4.2 for why rare-class counts may still be thin downstream.
    - Fully reproducible: same rows + same seed + same fractions always
      produce the same split (see `build_manifest`'s recorded seed/hash).
    """
    split_fractions = split_fractions or DEFAULT_SPLIT_FRACTIONS
    total = sum(split_fractions.values())
    if abs(total - 1.0) > 1e-6:
        raise DatasetPrepError(f"split_fractions must sum to 1.0, got {total}")
    if not rows:
        return SplitResult(train=[], val=[], test=[], config={
            "seed": seed, "split_fractions": split_fractions, "stratify_field": stratify_field,
            "n_groups": 0, "n_rows": 0, "group_level_split": True,
            "split_sizes": {name: 0 for name in split_fractions},
        })

    groups = build_dedup_groups(rows)
    rng = random.Random(seed)

    by_stratum: dict[str, list[tuple[str, list[dict]]]] = defaultdict(list)
    for key, group_rows in groups.items():
        labels_in_group = [r.get(stratify_field, "") for r in group_rows]
        majority = max(set(labels_in_group), key=labels_in_group.count)
        by_stratum[majority].append((key, group_rows))

    split_names = list(split_fractions.items())
    assigned: dict[str, list[dict]] = {name: [] for name, _ in split_names}

    for _stratum_label, items in by_stratum.items():
        rng.shuffle(items)
        n = len(items)
        counts = {}
        remaining = n
        for i, (name, frac) in enumerate(split_names):
            if i == len(split_names) - 1:
                counts[name] = remaining
            else:
                c = round(n * frac)
                counts[name] = min(c, remaining)
                remaining -= counts[name]
        cursor = 0
        for name, _ in split_names:
            take = counts[name]
            for _, group_rows in items[cursor:cursor + take]:
                assigned[name].extend(group_rows)
            cursor += take

    config = {
        "seed": seed,
        "split_fractions": split_fractions,
        "stratify_field": stratify_field,
        "n_groups": len(groups),
        "n_rows": len(rows),
        "group_level_split": True,
        "split_sizes": {name: len(assigned[name]) for name, _ in split_names},
    }
    return SplitResult(
        train=assigned.get("train", []), val=assigned.get("val", []), test=assigned.get("test", []),
        config=config,
    )


def verify_no_leakage(splits: SplitResult) -> list[str]:
    """Returns a list of human-readable problems; an empty list means the
    split is clean. Checks both duplicate-text leakage and ID leakage."""
    problems: list[str] = []
    seen_text: dict[str, str] = {}
    seen_id: dict[str, str] = {}
    for split_name, rows in splits.as_dict().items():
        for row in rows:
            text_key = _dedup_group_key(row)
            cid = row.get("comment_id")
            if text_key in seen_text and seen_text[text_key] != split_name:
                problems.append(
                    f"Duplicate-text leakage: a comment's text group appears in both "
                    f"'{seen_text[text_key]}' and '{split_name}' (comment_id={cid})"
                )
            seen_text[text_key] = split_name
            if cid in seen_id and seen_id[cid] != split_name:
                problems.append(
                    f"ID leakage: comment_id={cid} appears in both '{seen_id[cid]}' and "
                    f"'{split_name}'"
                )
            seen_id[cid] = split_name
    return problems


def _label_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for r in rows:
        counts[r.get("annotator_label", "")] += 1
    return dict(counts)


def _language_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for r in rows:
        counts[r.get("language", "")] += 1
    return dict(counts)


def build_manifest(splits: SplitResult, source_path: Path, excluded_rows: list[dict]) -> dict:
    source_path = Path(source_path)
    return {
        "generated_utc": ann_schema.utcnow_iso(),
        "source_file": str(source_path),
        "source_sha256": ann_schema.sha256_file(source_path) if source_path.exists() else None,
        "config": splits.config,
        "excluded_from_classification_count": len(excluded_rows),
        "excluded_by_reason": _label_counts(
            [{"annotator_label": r.get("exclusion_code", "")} for r in excluded_rows]
        ),
        "leakage_check": {"problems": verify_no_leakage(splits)},
        "label_distribution": {name: _label_counts(rows) for name, rows in splits.as_dict().items()},
        "language_distribution": {name: _language_counts(rows) for name, rows in splits.as_dict().items()},
        "no_model_trained": True,
        "no_pseudo_labels_used": True,
        "gold_standard_claim": "NOT MADE -- see docs/dataset/SINGLE_ANNOTATOR_PROTOCOL.md section 9.",
    }


def write_splits(splits: SplitResult, output_dir: Path) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for name, rows in splits.as_dict().items():
        out_path = output_dir / f"{name}.csv"
        ann_schema.write_rows_atomic(out_path, rows, SPLIT_COLUMNS)
        written[name] = out_path
    return written


def run(
    source_path: Path = DEFAULT_SOURCE_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    split_fractions: dict[str, float] | None = None,
    seed: int = DEFAULT_SPLIT_SEED,
) -> dict:
    rows = load_finalized_annotations(source_path)
    classification_rows = prepare_classification_rows(rows)
    _, excluded_rows = separate_labels_and_exclusions(rows)

    splits = make_splits(classification_rows, split_fractions=split_fractions, seed=seed)
    problems = verify_no_leakage(splits)
    if problems:
        raise DatasetPrepError(
            "Refusing to write a leaking split:\n" + "\n".join(problems)
        )

    written = write_splits(splits, output_dir)
    manifest = build_manifest(splits, source_path, excluded_rows)
    manifest_path = Path(output_dir) / "split_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return {"manifest": manifest, "manifest_path": str(manifest_path), "files": {k: str(v) for k, v in written.items()}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Prepare stance-classification train/val/test splits.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=DEFAULT_SPLIT_SEED)
    args = parser.parse_args(argv)

    try:
        result = run(source_path=args.source, output_dir=args.output_dir, seed=args.seed)
    except DatasetPrepError as e:
        print(f"Dataset preparation refused:\n{e}")
        return 1

    m = result["manifest"]
    print(f"Wrote splits to {args.output_dir}:")
    for name, size in m["config"]["split_sizes"].items():
        print(f"  {name}: {size} rows -> {result['files'][name]}")
    print(f"Manifest: {result['manifest_path']}")
    print(f"Leakage problems: {len(m['leakage_check']['problems'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

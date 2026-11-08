"""Phase C — independent validation of an already-written split directory.

Re-checks train/val/test CSVs and their manifest from scratch (not by
reusing dataset_prep.run()'s in-memory state), so a split directory can be
audited on its own, after the fact, by anyone -- including a later process
or a different person. Never re-derives or trusts the manifest's own
claims without re-computing them.

Run directly:
    python ml/stance_classification/validate_splits.py --dir data/processed/stance_classification_splits
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ml.stance_classification import dataset_prep as dp
from scripts.annotation import schema as ann_schema


def validate_split_directory(output_dir: Path) -> list[str]:
    """Returns a list of problems; empty = clean."""
    output_dir = Path(output_dir)
    problems: list[str] = []

    splits: dict[str, list[dict]] = {}
    for name in ("train", "val", "test"):
        path = output_dir / f"{name}.csv"
        if not path.exists():
            problems.append(f"Missing split file: {path}")
            continue
        splits[name] = ann_schema.read_rows(path)

    if len(splits) < 3:
        return problems  # can't check further without all three files

    # valid stance labels only, no exclusion codes should ever appear here
    for name, rows in splits.items():
        for row in rows:
            label = (row.get("annotator_label") or "").strip()
            excl = (row.get("exclusion_code") or "").strip()
            if excl:
                problems.append(f"{name}.csv contains an excluded row (comment_id={row.get('comment_id')}); "
                                 "classification splits must never include exclusion-coded rows")
            if label not in ann_schema.STANCE_LABELS:
                problems.append(f"{name}.csv has an invalid/missing annotator_label "
                                 f"'{label}' for comment_id={row.get('comment_id')}")

    split_result = dp.SplitResult(
        train=splits.get("train", []), val=splits.get("val", []), test=splits.get("test", []), config={}
    )
    problems += dp.verify_no_leakage(split_result)

    manifest_path = output_dir / "split_manifest.json"
    if not manifest_path.exists():
        problems.append(f"Missing manifest: {manifest_path}")
    else:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        recorded_sizes = manifest.get("config", {}).get("split_sizes", {})
        for name, rows in splits.items():
            if recorded_sizes.get(name) != len(rows):
                problems.append(
                    f"Manifest split_sizes['{name}']={recorded_sizes.get(name)} does not match "
                    f"actual row count {len(rows)} in {name}.csv"
                )
        if manifest.get("gold_standard_claim", "").startswith("NOT MADE") is False:
            problems.append("Manifest no longer carries the 'gold_standard_claim: NOT MADE' "
                             "statement -- this must never be removed or overwritten with a claim.")

    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Independently validate a stance-classification split directory.")
    parser.add_argument("--dir", type=Path, default=dp.DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)

    problems = validate_split_directory(args.dir)
    if problems:
        print(f"{len(problems)} problem(s) found in {args.dir}:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"No problems found in {args.dir}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

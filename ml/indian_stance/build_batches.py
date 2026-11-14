"""Phase D: build METADATA-ONLY annotation batches (no comment or tweet text).

Text is deliberately not copied: the project's own rights audit records MyGov and the tweets as
blocked (no evidenced reuse or annotation permission). ml/indian_stance/materialize_text.py adds
redacted text later, and only against a recorded clearance decision.

    python -m ml.indian_stance.build_batches mygov  --quality-dir data/processed/indian/mygov_quality_v2 \
        --out-dir data/annotations/indian/mygov_batch_v2
    python -m ml.indian_stance.build_batches tweets --plan data/processed/indian/tweets_split_v2/sampling_plan_1500_v2_PROPOSED.csv \
        --out-dir data/annotations/indian/tweets_batch_v2
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from ml.indian_stance import annotation_schema as S
from ml.indian_stance.common import (SourceError, new_output_dir, resolve_source_root, sha256_file, write_csv,
                                     write_manifest)

SEED = 20261114
ANNOTATORS = ("annotator_A", "annotator_B")


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def ordered(df: pd.DataFrame, batch_col: str, batch_order: list[str], seed: int) -> pd.DataFrame:
    """Batch blocks in a fixed order; deterministic shuffle within each block."""
    rng = np.random.default_rng(seed)
    parts = []
    for b in batch_order:
        part = df[df[batch_col] == b]
        parts.append(part.iloc[rng.permutation(len(part))])
    out = pd.concat(parts, ignore_index=True)
    if len(out) != len(df):
        raise ValueError(f"unexpected {batch_col} values: {sorted(set(df[batch_col]) - set(batch_order))}")
    out["annotation_order"] = [str(i) for i in range(1, len(out) + 1)]
    return out


def write_annotator_files(out_dir: Path, items: pd.DataFrame, fields: list[str], stem: str) -> None:
    write_csv(out_dir / f"{stem}_items.csv", items.to_dict("records"), [f for f in fields if f in items.columns])
    for a in ANNOTATORS:
        sheet = items.copy()
        for f in fields:
            if f not in sheet.columns:
                sheet[f] = ""
        write_csv(out_dir / f"{stem}_{a}.csv", sheet.to_dict("records"), fields)


def build_mygov(source_root: Path, quality_dir: Path, out_dir: Path) -> dict:
    P = source_root / "processed"
    inputs = {"clean": P / "mygov_comments_clean.csv",
              "template_v1_A": P / "mygov" / "annotation_v1" / "mygov_annotation_template_v1_annotator_A.csv"}
    groups = read_csv(quality_dir / "dedup_groups.csv")
    trunc = read_csv(quality_dir / "truncation_candidates.csv")
    pii = read_csv(quality_dir / "pii_review.csv")
    clean, tmpl = read_csv(inputs["clean"]), read_csv(inputs["template_v1_A"])
    members = [m for s in groups.member_comment_ids for m in s.split(";")]
    if len(members) != len(set(members)) or set(members) != set(clean.comment_id):
        raise ValueError("dedup groups do not partition the clean comment IDs")
    c = clean.set_index("comment_id")
    t = tmpl.set_index("comment_id")
    likely = set(trunc[trunc.truncation_class == "LIKELY_TRUNCATED"].comment_id)
    handling = pii.set_index("comment_id").proposed_handling.to_dict()
    items = pd.DataFrame({
        "source": "mygov", "batch_version": "mygov_batch_v2_PROPOSED",
        "legacy_annotation_batch": [t.annotation_batch[r] for r in groups.representative_comment_id],
        "representative_comment_id": groups.representative_comment_id, "member_comment_ids": groups.member_comment_ids,
        "group_size": groups.group_size,
        "possible_truncation": [str(any(m in likely for m in s.split(";"))) for s in groups.member_comment_ids],
        "has_attachment": [c.has_attachment[r] for r in groups.representative_comment_id],
        "script_detected": [c.script_detected[r] for r in groups.representative_comment_id],
        "pii_handling": [max((handling.get(m, "NONE") for m in s.split(";")),
                             key=["NONE", "AUTO_REDACT", "MANUAL_REVIEW"].index) for s in groups.member_comment_ids],
        "clause_numbers_detected": [t.clause_numbers_detected[r] for r in groups.representative_comment_id],
        "normalised_text_sha256": groups.normalised_text_sha256,
        "text_status": S.TEXT_STATUS_PENDING, "stance_target": S.MYGOV_STANCE_TARGET,
    })
    items = ordered(items, "legacy_annotation_batch", ["pilot_50", "main"], SEED)
    items.insert(0, "item_id", [f"MYG2-{i:04d}" for i in range(1, len(items) + 1)])
    out_dir = new_output_dir(out_dir)
    write_annotator_files(out_dir, items, S.MYGOV_BATCH_FIELDS, "mygov_batch_v2")
    summary = {"items": len(items), "source_comments_covered": len(members),
               "by_legacy_batch": items.legacy_annotation_batch.value_counts().to_dict(),
               "pii_handling": items.pii_handling.value_counts().to_dict(),
               "possible_truncation": int((items.possible_truncation == "True").sum()),
               "text_included": False}
    inputs.update({"dedup_groups": quality_dir / "dedup_groups.csv", "truncation": quality_dir / "truncation_candidates.csv",
                   "pii_review": quality_dir / "pii_review.csv"})
    write_manifest(out_dir, inputs, source_root, {
        "schema_version": S.SCHEMA_VERSION, "status": "PROPOSED — NOT ADOPTED; blank templates are not annotations",
        "seed": SEED, "summary": summary, "codebook": "docs/annotation/PROPOSED_INDIAN_STANCE_CODEBOOK_v2.md",
        "privacy": "metadata only; comment text not materialised", "builder": "ml/indian_stance/build_batches.py mygov"})
    return summary


def build_tweets(source_root: Path, plan_path: Path, out_dir: Path) -> dict:
    plan = read_csv(plan_path)
    if (plan.plan_version != "v2_PROPOSED_NOT_ADOPTED").any():
        raise ValueError("expected the v2 PROPOSED plan produced by ml/indian_stance/tweets_split.py")
    items = pd.DataFrame({
        "source": "tweets", "batch_version": "tweets_batch_v2_PROPOSED", "tweet_row_id": plan.tweet_row_id,
        "author_pseudo_id": plan.author_pseudo_id, "month": plan.month, "study_split": plan.study_split,
        "annotation_batch": plan.annotation_batch, "plan_v2_status": plan.v2_status,
        "masked_text_group": plan.masked_text_group, "script_detected": plan.script_detected,
        "text_status": S.TEXT_STATUS_PENDING})
    items = ordered(items, "annotation_batch", ["pilot_200", "main", "test"], SEED)
    items.insert(0, "item_id", [f"TWT2-{i:04d}" for i in range(1, len(items) + 1)])
    out_dir = new_output_dir(out_dir)
    write_annotator_files(out_dir, items, S.TWEET_BATCH_FIELDS, "tweets_batch_v2")
    summary = {"items": len(items), "by_batch": items.annotation_batch.value_counts().to_dict(),
               "by_split": items.study_split.value_counts().to_dict(), "text_included": False}
    write_manifest(out_dir, {"clean": source_root / "processed" / "kaggle_indian_politics_tweets_clean.csv"}, source_root, {
        "schema_version": S.SCHEMA_VERSION, "status": "PROPOSED — NOT ADOPTED; blank templates are not annotations",
        "seed": SEED, "summary": summary, "plan": {"path": plan_path.as_posix(), "sha256": sha256_file(plan_path)},
        "guide": "docs/annotation/PROPOSED_TWEET_STANCE_GUIDE_v1.md",
        "privacy": "metadata only; tweet text not materialised", "builder": "ml/indian_stance/build_batches.py tweets"})
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="kind", required=True)
    m = sub.add_parser("mygov")
    m.add_argument("--quality-dir", required=True)
    t = sub.add_parser("tweets")
    t.add_argument("--plan", required=True)
    for p in (m, t):
        p.add_argument("--source-root")
        p.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    try:
        root = resolve_source_root(a.source_root)
        s = (build_mygov(root, Path(a.quality_dir), Path(a.out_dir)) if a.kind == "mygov"
             else build_tweets(root, Path(a.plan), Path(a.out_dir)))
    except (SourceError, FileExistsError, ValueError, KeyError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    print(s)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())

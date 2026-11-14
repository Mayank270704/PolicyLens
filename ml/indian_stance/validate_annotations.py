"""Validate an Indian stance annotation sheet: schema, allowed labels, label consistency,
duplicates, provenance against the OLD source files, and (tweets) split leakage.

    python -m ml.indian_stance.validate_annotations data/annotations/indian/mygov_batch_v2/mygov_batch_v2_annotator_A.csv
    python -m ml.indian_stance.validate_annotations <sheet.csv> --no-source-check

Exit code 0 = no errors, 1 = errors found, 2 = could not run. Blank rows are unannotated, not invalid,
and are never counted as annotations.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from ml.indian_stance import annotation_schema as S
from ml.indian_stance.common import SourceError, norm_text, norm_tweet, resolve_source_root, sha256_text


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def check_structure(df: pd.DataFrame, kind: str) -> list[str]:
    fields = S.MYGOV_BATCH_FIELDS if kind == "mygov" else S.TWEET_BATCH_FIELDS
    errs = [f"missing column: {c}" for c in fields if c not in df.columns]
    if "item_id" in df.columns and df.item_id.duplicated().any():
        errs.append(f"duplicate item_id: {sorted(df.item_id[df.item_id.duplicated()].unique())[:10]}")
    if kind == "mygov" and "member_comment_ids" in df.columns:
        ids = [m for s in df.member_comment_ids for m in s.split(";") if m]
        dup = sorted({m for m in ids if ids.count(m) > 1})
        if dup:
            errs.append(f"comment_id in more than one item: {dup[:10]}")
        bad_rep = df[[r not in s.split(";") for r, s in zip(df.representative_comment_id, df.member_comment_ids)]]
        if len(bad_rep):
            errs.append(f"representative not among members for {len(bad_rep)} items")
        if (df.get("stance_target", pd.Series(dtype=str)) != S.MYGOV_STANCE_TARGET).any():
            errs.append(f"stance_target must be {S.MYGOV_STANCE_TARGET} for every MyGov item")
    if kind == "tweets" and "tweet_row_id" in df.columns and df.tweet_row_id.duplicated().any():
        errs.append("duplicate tweet_row_id")
    return errs


def check_split_leakage(df: pd.DataFrame) -> list[str]:
    t, o = df[df.study_split == "locked_test_300"], df[df.study_split != "locked_test_300"]
    errs = []
    for col in ("author_pseudo_id", "masked_text_group"):
        x = set(t[col]) & set(o[col])
        if x:
            errs.append(f"{col} crosses locked test and train_dev: {len(x)} value(s)")
    return errs


def check_provenance(df: pd.DataFrame, kind: str, source_root: Path) -> list[str]:
    P = source_root / "processed"
    errs = []
    if kind == "mygov":
        clean = read_csv(P / "mygov_comments_clean.csv").set_index("comment_id")
        for _, r in df.iterrows():
            members = r.member_comment_ids.split(";")
            missing = [m for m in members if m not in clean.index]
            if missing:
                errs.append(f"{r.item_id}: unknown source comment_id(s) {missing}")
                continue
            hashes = {sha256_text(norm_text(clean.comment_text[m])) for m in members}
            if hashes != {r.normalised_text_sha256}:
                errs.append(f"{r.item_id}: normalised_text_sha256 does not match source text")
    else:
        clean = read_csv(P / "kaggle_indian_politics_tweets_clean.csv").set_index("tweet_row_id")
        for _, r in df.iterrows():
            if r.tweet_row_id not in clean.index:
                errs.append(f"{r.item_id}: unknown tweet_row_id {r.tweet_row_id}")
                continue
            if clean.author_pseudo_id[r.tweet_row_id] != r.author_pseudo_id:
                errs.append(f"{r.item_id}: author_pseudo_id does not match source")
            if sha256_text(norm_tweet(clean.tweet_text[r.tweet_row_id]))[:16] != r.masked_text_group:
                errs.append(f"{r.item_id}: masked_text_group does not match source text")
    return errs


def validate(path: Path, source_root: Path | None) -> dict:
    df = read_csv(path)
    if "source" not in df.columns or df.source.nunique() != 1 or df.source.iloc[0] not in ("mygov", "tweets"):
        return {"file": str(path), "errors": ["column 'source' must be a single value: mygov or tweets"], "ok": False}
    kind = df.source.iloc[0]
    errors = check_structure(df, kind)
    if kind == "tweets" and not errors:
        errors += check_split_leakage(df)
    if source_root is not None and not errors:
        errors += check_provenance(df, kind, source_root)
    rows = df.to_dict("records")
    annotated = [r for r in rows if S.is_annotated(r, kind)]
    for r in annotated:
        errors += [f"{r['item_id']}: {e}" for e in S.validate_label_row(r, kind)]
    ann_ids = {str(r.get("annotator_id", "")).strip() for r in annotated} - {""}
    if len(ann_ids) > 1:
        errors.append(f"more than one annotator_id in one sheet: {sorted(ann_ids)}")
    labelled = [r for r in annotated if r.get("stance")]
    return {"file": str(path), "kind": kind, "schema_version": S.SCHEMA_VERSION, "items": len(rows),
            "annotated_rows": len(annotated), "unannotated_rows": len(rows) - len(annotated),
            "stance_counts": pd.Series([r["stance"] for r in labelled], dtype=str).value_counts().to_dict(),
            "exclusion_counts": pd.Series([r["exclusion_code"] for r in annotated if r.get("exclusion_code")], dtype=str).value_counts().to_dict(),
            "provenance_checked": source_root is not None, "errors": errors[:200], "error_count": len(errors),
            "ok": not errors}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sheet", nargs="+")
    ap.add_argument("--source-root")
    ap.add_argument("--no-source-check", action="store_true", help="skip provenance checks against OLD source files")
    a = ap.parse_args(argv)
    try:
        root = None if a.no_source_check else resolve_source_root(a.source_root)
    except SourceError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    ok = True
    for s in a.sheet:
        res = validate(Path(s), root)
        ok &= res["ok"]
        print(json.dumps(res, indent=1, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())

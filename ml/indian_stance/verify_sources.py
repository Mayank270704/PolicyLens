"""Phase A: verify the Indian source files and the counts reported by the 2026-11-14 audit.

Writes one row per checked fact (file, metric, verified value, expected value, status).
No comment or tweet text is written.

    python -m ml.indian_stance.verify_sources --out reports/INDIAN_DATASET_VERIFICATION.csv
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from ml.indian_stance.common import (SourceError, norm_text, resolve_source_root, sha256_file, source_label,
                                     write_csv)

FIELDS = ["source", "role", "file", "format", "size_bytes", "sha256", "recorded_sha256", "sha256_match",
          "metric", "verified_value", "expected_value", "status", "note"]


def audit_norm_ws(s: str) -> str:
    """Audit rule for the distinct-text count: whitespace collapse + lowercase only."""
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def audit_norm(s: str) -> str:
    """Audit rule for the split-crossing check: mentions/URLs removed, whitespace, lowercase."""
    return re.sub(r"\s+", " ", re.sub(r"https?://\S+|@\w+", " ", str(s))).strip().lower()


def read_csv(path: Path, **kw) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig", **kw)


class Recorder:
    def __init__(self, root: Path, max_hash_mb: float):
        self.root, self.max_hash_mb, self.rows, self._hash = root, max_hash_mb, [], {}

    def file_meta(self, path: Path, recorded: str | None):
        size = path.stat().st_size
        if path not in self._hash:
            self._hash[path] = sha256_file(path) if size <= self.max_hash_mb * 1e6 else None
        sha = self._hash[path]
        match = "" if not recorded else ("not_recomputed" if sha is None else str(sha == recorded))
        return size, sha or f"not computed (> {self.max_hash_mb:g} MB)", recorded or "", match

    def add(self, source, role, path, metric, value, expected=None, note="", recorded=None):
        size, sha, rec, match = self.file_meta(path, recorded)
        if expected is None:
            status = "RECORDED"
        else:
            status = "VERIFIED" if str(value) == str(expected) else "DISCREPANCY"
        if match == "False":
            status = "DISCREPANCY"
        self.rows.append({"source": source, "role": role, "file": source_label(path, self.root),
                          "format": path.suffix.lstrip("."), "size_bytes": size, "sha256": sha,
                          "recorded_sha256": rec, "sha256_match": match, "metric": metric,
                          "verified_value": value, "expected_value": "" if expected is None else expected,
                          "status": status, "note": note})


def check_mygov(r: Recorder, root: Path) -> None:
    P = root / "processed"
    ext = json.loads((P / "mygov_extraction_summary.json").read_text(encoding="utf-8"))["outputs_sha256"]
    src, role = "MyGov", "consultation comments (only Indian consultation-comment source)"
    raw = read_csv(P / "mygov_comments_raw.csv")
    r.add(src, role, P / "mygov_comments_raw.csv", "rows", len(raw), 560, recorded=ext["mygov_comments_raw.csv"])
    r.add(src, role, P / "mygov_comments_raw.csv", "unique_comment_ids", raw.comment_id.nunique(), 550)
    r.add(src, role, P / "mygov_comments_raw.csv", "duplicate_id_records", int((raw.is_duplicate_id == "True").sum()), 10)
    c = read_csv(P / "mygov_comments_clean.csv")
    f = P / "mygov_comments_clean.csv"
    r.add(src, role, f, "rows", len(c), 550, recorded=ext["mygov_comments_clean.csv"])
    r.add(src, role, f, "unique_comment_ids", c.comment_id.nunique(), 550)
    r.add(src, role, f, "distinct_texts_exact", c.comment_text.nunique(), 542)
    r.add(src, role, f, "distinct_texts_normalised", c.comment_text.map(norm_text).nunique(), 541,
          note="NFKC + whitespace + lowercase (OLD project's duplicate-group rule)")
    r.add(src, role, f, "empty_texts", int((c.comment_text.str.strip() == "").sum()), 0)
    r.add(src, role, f, "consultations", c.consultation_title.nunique(), 1)
    r.add(src, role, f, "near_500_char_limit", int((c.near_500_char_limit == "True").sum()), 98)
    r.add(src, role, f, "near_limit_and_no_terminal_punctuation",
          int(((c.near_500_char_limit == "True") & (c.ends_without_terminal_punctuation == "True")).sum()), 49)
    r.add(src, role, f, "language_column_empty", int((c.language.str.strip() == "").sum()), 550)
    r.add(src, role, f, "submission_date_empty", int((c.submission_date.str.strip() == "").sum()), 550)
    pii = read_csv(P / "mygov_pii_review_flags.csv")
    r.add(src, role, P / "mygov_pii_review_flags.csv", "pii_any_flag", int((pii.any_flag == "True").sum()), 23)
    inv = read_csv(P / "mygov_page_inventory.csv")
    f = P / "mygov_page_inventory.csv"
    r.add(src, role, f, "saved_html_pages", len(inv), 56, recorded=ext["mygov_page_inventory.csv"])
    r.add(src, role, f, "displayed_total_submissions", "|".join(sorted(inv.displayed_total_submissions.unique())), "1132",
          note="page's displayed count, NOT a recovered count")
    for name in ("mygov_annotation_pool_blank.csv",):
        d = read_csv(P / name)
        r.add(src, "blank annotation pool (OLD)", P / name, "filled_stance_labels", int((d.stance.str.strip() != "").sum()), 0)
    for k in ("A", "B"):
        p = P / "mygov" / "annotation_v1" / f"mygov_annotation_template_v1_annotator_{k}.csv"
        d = read_csv(p)
        r.add(src, "blank annotation template (OLD)", p, "rows", len(d), 550,
              recorded="91f09e9c77cb69e502a76617413e699dadb93399a123b9bc867e9672a270becc")
        r.add(src, "blank annotation template (OLD)", p, "filled_stance_labels", int((d.stance.str.strip() != "").sum()), 0)
        r.add(src, "blank annotation template (OLD)", p, "stance_label_set_in_codebook_v1",
              "Support|Oppose|Mixed|Neutral|Unclear", note="5 labels incl. Mixed; project objective is 4 classes")


def check_tweets(r: Recorder, root: Path) -> None:
    P = root / "processed"
    src, role = "Tweets (Kaggle Indian politics)", "social-media posts; separate source"
    raw_p = root / "kaggle" / "Dataset of Indian Politics Tweets & Reactions" / "tweets.csv"
    n = sum(len(ch) for ch in read_csv(raw_p, chunksize=20000, usecols=["Tweet"]))
    r.add(src, role, raw_p, "csv_records", n, 50001, note="includes 1 split-line fragment repaired in the clean file")
    f = P / "kaggle_indian_politics_tweets_clean.csv"
    ann_man = json.loads((P / "tweets" / "annotation_v1" / "manifest.json").read_text(encoding="utf-8"))
    c = read_csv(f, usecols=["tweet_row_id", "created_at_utc", "author_pseudo_id", "tweet_text"])
    r.add(src, role, f, "rows", len(c), 50000, recorded=ann_man["source_sha256"])
    r.add(src, role, f, "unique_tweet_row_ids", c.tweet_row_id.nunique(), 50000)
    r.add(src, role, f, "distinct_texts_exact", c.tweet_text.nunique(), 49569)
    r.add(src, role, f, "distinct_texts_whitespace_case_normalised", c.tweet_text.map(audit_norm_ws).nunique(), 49530,
          note="audit rule: whitespace collapse + lowercase")
    r.add(src, role, f, "distinct_texts_mentions_urls_removed", c.tweet_text.map(audit_norm).nunique(),
          note="leakage-relevant: replies/retweets differing only in @mentions or URLs collapse")
    r.add(src, role, f, "empty_texts", int((c.tweet_text.str.strip() == "").sum()), 0)
    r.add(src, role, f, "pseudonymous_authors", c.author_pseudo_id.nunique(), 35109)
    ts = pd.to_datetime(c.created_at_utc, utc=True)
    r.add(src, role, f, "date_min", str(ts.min().date()), "2022-10-15")
    r.add(src, role, f, "date_max", str(ts.max().date()), "2023-03-29")
    plan_p = P / "tweets" / "annotation_v1" / "sampling_plan_1500.csv"
    plan = read_csv(plan_p)
    rec = ann_man["outputs_sha256"]["sampling_plan_1500.csv"]
    r.add(src, "sampling plan (OLD)", plan_p, "rows", len(plan), 1500, recorded=rec)
    r.add(src, "sampling plan (OLD)", plan_p, "locked_test_rows", int((plan.study_split == "locked_test_300").sum()), 300)
    m = plan.merge(c, on="tweet_row_id", how="left", suffixes=("", "_c"))
    t = m.study_split == "locked_test_300"
    r.add(src, "sampling plan (OLD)", plan_p, "authors_crossing_test_and_train_dev",
          len(set(m[t].author_pseudo_id) & set(m[~t].author_pseudo_id)), 6)
    nt = m.tweet_text.map(audit_norm)
    r.add(src, "sampling plan (OLD)", plan_p, "audit_normalised_texts_crossing_test_and_train_dev",
          len(set(nt[t]) & set(nt[~t])), 2)
    for k in ("A", "B"):
        p = P / "tweets" / "annotation_v1" / f"tweets_pilot_annotation_template_v1_annotator_{k}.csv"
        d = read_csv(p)
        r.add(src, "blank pilot template (OLD)", p, "rows", len(d), 200,
              recorded=ann_man["outputs_sha256"][p.name])
        r.add(src, "blank pilot template (OLD)", p, "filled_sentiment_labels", int((d.sentiment.str.strip() != "").sum()), 0,
              note="template has a sentiment column and no stance column")
    w = P / "tweets" / "weak_labels_sentiment140_v1" / "weak_predictions.csv"
    d = read_csv(w)
    r.add("Weak sentiment predictions (QUARANTINED)", "model output, NOT ground truth, never stance", w, "rows", len(d), 50000,
          recorded="1af658505ea2e6da8ef4fe5fd8639e4976d8d0363245a52e857eea1723f20468")
    r.add("Weak sentiment predictions (QUARANTINED)", "model output, NOT ground truth, never stance", w, "label_values",
          "|".join(sorted(d.weak_label.unique())), "negative|positive")
    r.add("Weak sentiment predictions (QUARANTINED)", "model output, NOT ground truth, never stance", w,
          "rows_marked_not_ground_truth", int(d.label_source.str.contains("NOT_ground_truth").sum()), 50000)


def check_context(r: Recorder, root: Path) -> None:
    P = root / "processed"
    src, role = "CIVIS", "policy documents + reference summaries; retrieval/context only"
    total = 0
    for sp, exp in (("train", 136), ("test", 34)):
        p = root / "huggingface_datasets" / "civis_consultation_summaries" / f"{sp}.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        r.add(src, role, p, "records", len(d["Text"]), exp)
        total += len(d["Text"])
    c = read_csv(P / "civis_policy_documents_clean.csv")
    r.add(src, role, P / "civis_policy_documents_clean.csv", "rows", len(c), 170)
    r.add(src, role, P / "civis_policy_documents_clean.csv", "empty_document_text",
          int((c.document_text.str.strip() == "").sum()), 4)
    r.add(src, role, P / "civis_policy_documents_clean.csv", "stance_or_sentiment_columns",
          len([x for x in c.columns if re.search(r"stance|sentiment|label", x, re.I)]), 0)
    src, role = "Lok Sabha Q&A", "parliamentary Q&A; retrieval/context only"
    integ = root.parent / "data" / "dataset_integration_assessments" / "run_lok_sabha_v1" / "manifest.json"
    rec = {}
    if integ.exists():
        rec = {Path(k).name: v["sha256"] for k, v in json.loads(integ.read_text(encoding="utf-8"))["inputs_sha256"].items()}
    shard_total = 0
    for p in sorted((root / "huggingface_datasets" / "lok-sabha-qa").glob("*.parquet")):
        shard_total += pq.ParquetFile(p).metadata.num_rows
    first = sorted((root / "huggingface_datasets" / "lok-sabha-qa").glob("*.parquet"))[0]
    r.add(src, role, first, "rows_all_5_shards_from_parquet_metadata", shard_total, 150808, note="shards not re-hashed")
    f = P / "lok_sabha_qa_clean.parquet"
    r.add(src, role, f, "rows", pq.ParquetFile(f).metadata.num_rows, 150808, recorded=rec.get(f.name))
    ids = pq.read_table(f, columns=["qa_id"]).column(0).to_pandas()
    r.add(src, role, f, "unique_qa_id", ids.nunique(), 150808)
    f = P / "lok_sabha_qa_metadata.csv"
    r.add(src, role, f, "rows", sum(len(ch) for ch in read_csv(f, chunksize=50000, usecols=["qa_id"])), 150808,
          recorded=rec.get(f.name))


def check_sentiment140(r: Recorder, root: Path) -> None:
    base = root.parent / "trainingandtestdata"
    src, role = "Sentiment140 (QUARANTINED)", "sentiment-only; never stance ground truth"
    cols = ["polarity", "id", "date", "query", "user", "text"]
    p = base / "training.1600000.processed.noemoticon.csv"
    counts: dict[str, int] = {}
    for ch in pd.read_csv(p, header=None, names=cols, usecols=["polarity"], dtype=str, encoding="latin-1", chunksize=400000):
        for k, v in ch.polarity.value_counts().items():
            counts[k] = counts.get(k, 0) + int(v)
    r.add(src, role, p, "rows", sum(counts.values()), 1600000)
    r.add(src, role, p, "polarity_values", "|".join(f"{k}:{counts[k]}" for k in sorted(counts)), "0:800000|4:800000")
    p = base / "testdata.manual.2009.06.14.csv"
    d = pd.read_csv(p, header=None, names=cols, dtype=str, encoding="latin-1")
    r.add(src, role, p, "rows", len(d), 498)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source-root", help="OLD workspace indian/ folder (default: env or ../dataset/indian)")
    ap.add_argument("--out", required=True, help="CSV to create (must not exist)")
    ap.add_argument("--max-hash-mb", type=float, default=300.0)
    a = ap.parse_args(argv)
    try:
        root = resolve_source_root(a.source_root)
    except SourceError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    out = Path(a.out)
    if out.exists():
        print(f"[ERROR] {out} exists; refusing to overwrite", file=sys.stderr)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    r = Recorder(root, a.max_hash_mb)
    for fn in (check_mygov, check_tweets, check_context, check_sentiment140):
        fn(r, root)
    write_csv(out, r.rows, FIELDS)
    bad = [x for x in r.rows if x["status"] == "DISCREPANCY"]
    print(f"{len(r.rows)} checks: {sum(x['status'] == 'VERIFIED' for x in r.rows)} verified, "
          f"{len(bad)} discrepancies, {sum(x['status'] == 'RECORDED' for x in r.rows)} recorded-only -> {out}")
    for x in bad:
        print(f"  DISCREPANCY {x['source']} {x['metric']}: verified={x['verified_value']} expected={x['expected_value']} "
              f"sha_match={x['sha256_match']}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())

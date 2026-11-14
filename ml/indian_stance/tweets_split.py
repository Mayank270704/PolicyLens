"""Phase B/D: tweet data quality, reproduction of the OLD 1,500-row sampling plan, split-leakage
review, and a PROPOSED (not adopted) leakage-safe v2 plan.

The locked 300-row test set is never changed. Only train_dev rows that leak into it (same author,
same masked-normalised text, or near-duplicate text) are replaced, using the original sampling
rules and order. Outputs hold IDs, splits, flags and hashes only; no tweet text.

    python -m ml.indian_stance.tweets_split --out-dir data/processed/indian/tweets_split_v2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from ml.indian_stance.common import (SourceError, jaccard, new_output_dir, norm_tweet, resolve_source_root, sha256_text,
                                     token_set, write_csv, write_json, write_manifest)

NEAR_DUP_JACCARD = 0.8
PLAN_COLS = ["tweet_row_id", "created_at_utc", "month", "author_pseudo_id", "script_detected",
             "exact_text_duplicate_group", "study_split", "annotation_batch"]


def load_clean(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig",
                    usecols=["tweet_row_id", "created_at_utc", "author_pseudo_id", "tweet_text", "script_detected",
                             "exact_text_duplicate_group"])
    d["month"] = pd.to_datetime(d.created_at_utc, utc=True, errors="coerce").dt.strftime("%Y-%m")
    d["masked_group"] = d.tweet_text.map(lambda t: sha256_text(norm_tweet(t))[:16])
    d["tokens"] = d.tweet_text.map(lambda t: token_set(norm_tweet(t)))
    return d


def original_selection(d: pd.DataFrame, size: int = 1500, test: int = 300, pilot: int = 200, seed: int = 42):
    """Faithful re-implementation of OLD indian/scripts/run_tweets_analysis_v1.py:annotation()."""
    rng = np.random.default_rng(seed)
    cand = d[(d.exact_text_duplicate_group == "") | ~d.duplicated("exact_text_duplicate_group")]
    cand = cand.iloc[rng.permutation(len(cand))]
    cand = cand[cand.groupby("author_pseudo_id").cumcount() < 2]
    months = sorted(cand.month.dropna().unique())
    per_month = int(np.ceil(size / len(months)))
    study = pd.concat([g.head(per_month) for _, g in cand.groupby("month")]).head(size)
    study = study.iloc[rng.permutation(len(study))].reset_index(drop=True)
    study["study_split"] = np.where(np.arange(len(study)) < test, "locked_test_300", "train_dev")
    pilot_ids = set(study[study.study_split == "train_dev"].tweet_row_id.head(pilot))
    study["annotation_batch"] = np.where(study.tweet_row_id.isin(pilot_ids), "pilot_200",
                                         np.where(study.study_split == "locked_test_300", "test", "main"))
    return study, cand


def near_dup_hits(tokens: frozenset, against: list[frozenset], thr: float = NEAR_DUP_JACCARD) -> int:
    return sum(jaccard(tokens, t) >= thr for t in against)


def leakage(plan: pd.DataFrame, test_split: str = "locked_test_300") -> dict:
    t, o = plan[plan.study_split == test_split], plan[plan.study_split != test_split]
    tt = list(t.tokens)
    nd_pairs = sum(near_dup_hits(x, tt) for x in o.tokens)
    return {"authors_crossing": len(set(t.author_pseudo_id) & set(o.author_pseudo_id)),
            "masked_text_groups_crossing": len(set(t.masked_group) & set(o.masked_group)),
            "near_duplicate_pairs_crossing": int(nd_pairs),
            "train_dev_rows_affected": int((o.author_pseudo_id.isin(set(t.author_pseudo_id)) |
                                            o.masked_group.isin(set(t.masked_group)) |
                                            o.tokens.map(lambda x: near_dup_hits(x, tt) > 0)).sum())}


def propose_v2(plan: pd.DataFrame, cand: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    test = plan[plan.study_split == "locked_test_300"]
    t_auth, t_grp, t_tok = set(test.author_pseudo_id), set(test.masked_group), list(test.tokens)
    kept = test.copy()
    kept["v2_status"] = "locked_test_unchanged"
    kept["replaces_tweet_row_id"] = ""
    used_ids = set(plan.tweet_row_id)
    grp_in_plan = set(test.masked_group)
    exact_in_plan = set(x for x in test.exact_text_duplicate_group if x)
    author_count = test.author_pseudo_id.value_counts().to_dict()

    def ok(r) -> bool:
        return (r.author_pseudo_id not in t_auth and r.masked_group not in grp_in_plan
                and (not r.exact_text_duplicate_group or r.exact_text_duplicate_group not in exact_in_plan)
                and author_count.get(r.author_pseudo_id, 0) < 2 and near_dup_hits(r.tokens, t_tok) == 0)

    def take(r):
        grp_in_plan.add(r.masked_group)
        if r.exact_text_duplicate_group:
            exact_in_plan.add(r.exact_text_duplicate_group)
        author_count[r.author_pseudo_id] = author_count.get(r.author_pseudo_id, 0) + 1

    rows, changes, removed = [], [], []
    for _, r in plan[plan.study_split == "train_dev"].iterrows():
        if ok(r):
            take(r)
            rows.append({**r.to_dict(), "v2_status": "kept", "replaces_tweet_row_id": ""})
        else:
            reasons = [n for n, c in (("author_in_locked_test", r.author_pseudo_id in t_auth),
                                      ("masked_text_group_in_plan", r.masked_group in grp_in_plan),
                                      ("near_duplicate_of_locked_test", near_dup_hits(r.tokens, t_tok) > 0)) if c]
            removed.append((r, ";".join(reasons) or "author_cap"))
    pool = cand[~cand.tweet_row_id.isin(used_ids)]
    for r, reason in removed:
        repl = None
        for _, c in pool[pool.month == r.month].iterrows():
            if c.tweet_row_id not in used_ids and ok(c):
                repl = c
                break
        if repl is None:
            changes.append({"removed_tweet_row_id": r.tweet_row_id, "reason": reason, "month": r.month,
                            "annotation_batch": r.annotation_batch, "replacement_tweet_row_id": ""})
            continue
        used_ids.add(repl.tweet_row_id)
        take(repl)
        rows.append({**repl.to_dict(), "study_split": "train_dev", "annotation_batch": r.annotation_batch,
                     "v2_status": "replacement", "replaces_tweet_row_id": r.tweet_row_id})
        changes.append({"removed_tweet_row_id": r.tweet_row_id, "reason": reason, "month": r.month,
                        "annotation_batch": r.annotation_batch, "replacement_tweet_row_id": repl.tweet_row_id})
    v2 = pd.concat([kept, pd.DataFrame(rows)], ignore_index=True)
    return v2, changes


def run(source_root: Path, out_dir: Path) -> dict:
    P = source_root / "processed"
    inputs = {"clean": P / "kaggle_indian_politics_tweets_clean.csv",
              "plan_v1": P / "tweets" / "annotation_v1" / "sampling_plan_1500.csv"}
    d = load_clean(inputs["clean"])
    old = pd.read_csv(inputs["plan_v1"], dtype=str, keep_default_na=False)
    out_dir = new_output_dir(out_dir)

    study, cand = original_selection(d)
    repro = {"rows_equal": len(study) == len(old),
             "same_ids_same_order": study.tweet_row_id.tolist() == old.tweet_row_id.tolist(),
             "same_split_and_batch": bool((study[["study_split", "annotation_batch"]].values ==
                                           old[["study_split", "annotation_batch"]].values).all())
             if len(study) == len(old) else False}
    plan = old.merge(d[["tweet_row_id", "tweet_text", "masked_group", "tokens"]], on="tweet_row_id", how="left")
    if plan.tweet_text.isna().any():
        raise ValueError("sampling plan references tweet_row_ids missing from the clean file")

    groups = d.masked_group.value_counts()
    quality = {"rows": len(d), "unique_tweet_row_ids": int(d.tweet_row_id.nunique()),
               "legacy_exact_duplicate_groups": int(d.exact_text_duplicate_group.replace("", np.nan).nunique()),
               "legacy_rows_in_exact_duplicate_groups": int((d.exact_text_duplicate_group != "").sum()),
               "masked_normalised_groups": int(len(groups)), "masked_groups_with_2plus": int((groups > 1).sum()),
               "rows_in_masked_groups_with_2plus": int(groups[groups > 1].sum()), "largest_masked_group": int(groups.max()),
               "authors": int(d.author_pseudo_id.nunique()), "authors_with_2plus_tweets": int((d.author_pseudo_id.value_counts() > 1).sum()),
               "tweets_per_month": {k: int(v) for k, v in d.month.value_counts().sort_index().items()},
               "script_detected": {k: int(v) for k, v in d.script_detected.value_counts().items()}}

    test = plan[plan.study_split == "locked_test_300"]
    rest = d[~d.tweet_row_id.isin(plan.tweet_row_id)]
    beyond = {"locked_test_authors_with_tweets_outside_plan": int(test.author_pseudo_id.isin(set(rest.author_pseudo_id)).sum()),
              "outside_plan_tweets_by_locked_test_authors": int(rest.author_pseudo_id.isin(set(test.author_pseudo_id)).sum()),
              "locked_test_masked_groups_with_members_outside_plan": int(test.masked_group.isin(set(rest.masked_group)).sum()),
              "outside_plan_tweets_in_locked_test_masked_groups": int(rest.masked_group.isin(set(test.masked_group)).sum())}
    within_plan_masked_dups = int(plan.masked_group.duplicated(keep=False).sum())

    v1_leak = leakage(plan)
    v2, changes = propose_v2(plan, cand)
    v2_leak = leakage(v2)
    v2_out = v2[PLAN_COLS + ["v2_status", "replaces_tweet_row_id", "masked_group"]].rename(columns={"masked_group": "masked_text_group"})
    v2_out["plan_version"] = "v2_PROPOSED_NOT_ADOPTED"
    write_csv(out_dir / "sampling_plan_1500_v2_PROPOSED.csv", v2_out.to_dict("records"), list(v2_out.columns))
    write_csv(out_dir / "v2_changes.csv", changes,
              ["removed_tweet_row_id", "reason", "month", "annotation_batch", "replacement_tweet_row_id"])

    counts = lambda p: {"rows": int(len(p)), "by_split": {k: int(v) for k, v in p.study_split.value_counts().items()},
                        "by_batch": {k: int(v) for k, v in p.annotation_batch.value_counts().items()},
                        "by_month": {k: int(v) for k, v in p.month.value_counts().sort_index().items()},
                        "by_script": {k: int(v) for k, v in p.script_detected.value_counts().items()},
                        "max_tweets_per_author": int(p.author_pseudo_id.value_counts().max()),
                        "masked_groups_repeated_within_plan": int(p.masked_group.duplicated(keep=False).sum())}
    v1_test_ids = set(test.tweet_row_id)
    summary = {
        "quality": quality, "reproduction_of_original_plan": repro,
        "original_plan": {**counts(plan), "leakage_vs_locked_test": v1_leak,
                          "within_plan_rows_sharing_masked_group": within_plan_masked_dups},
        "locked_test_vs_rest_of_corpus": beyond,
        "v2_proposed": {**counts(v2), "leakage_vs_locked_test": v2_leak,
                        "locked_test_identical_to_v1": set(v2[v2.study_split == "locked_test_300"].tweet_row_id) == v1_test_ids,
                        "train_dev_rows_replaced": sum(1 for c in changes if c["replacement_tweet_row_id"]),
                        "train_dev_rows_removed_without_replacement": sum(1 for c in changes if not c["replacement_tweet_row_id"]),
                        "pilot_200_rows_changed": sum(1 for c in changes if c["annotation_batch"] == "pilot_200"),
                        "status": "PROPOSED — NOT ADOPTED; original plan unchanged"},
        "near_duplicate_rule": f"token-set Jaccard >= {NEAR_DUP_JACCARD} on mention/URL-masked, NFKC-normalised text",
    }
    write_json(out_dir / "summary.json", summary)
    write_manifest(out_dir, inputs, source_root, {"script": "ml/indian_stance/tweets_split.py",
                                                  "privacy": "IDs, splits, flags and text-group hashes only; no tweet text",
                                                  "seed": 42})
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source-root")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    try:
        s = run(resolve_source_root(a.source_root), Path(a.out_dir))
    except (SourceError, FileExistsError, ValueError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    print(json.dumps(s, indent=1))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())

"""Group-aware, stratified, seeded train/validation/test assignment plus a leakage checker.

Rows sharing an item_id, text_group_id or author_group_id are joined into one component
(union-find) and a component is always assigned to a single split. A pre-registered locked test
(split == 'locked_test') is honoured as-is; a component spanning locked and non-locked rows is refused.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ml.indian_stance.common import jaccard, norm_tweet, token_set

GROUP_KEYS = ("item_id", "text_group_id", "author_group_id")


class LeakageError(ValueError):
    pass


def components(df: pd.DataFrame, keys=GROUP_KEYS) -> pd.Series:
    parent = list(range(len(df)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for k in keys:
        if k not in df.columns:
            continue
        first: dict[str, int] = {}
        for i, v in enumerate(df[k].tolist()):
            if not v:
                continue
            if v in first:
                a, b = find(i), find(first[v])
                if a != b:
                    parent[a] = b
            else:
                first[v] = i
    roots = [find(i) for i in range(len(df))]
    remap = {r: n for n, r in enumerate(dict.fromkeys(roots))}
    return pd.Series([f"C{remap[r]:05d}" for r in roots], index=df.index)


def _stratified_pick(comp_labels: pd.Series, fraction: float, rng: np.random.Generator) -> set[str]:
    """Pick ~fraction of components per majority-label stratum (at least 1 if the stratum has >= 2)."""
    chosen: set[str] = set()
    for _, comps in comp_labels.groupby(comp_labels):
        ids = sorted(comps.index)
        rng.shuffle(ids)
        n = int(round(len(ids) * fraction))
        if n == 0 and len(ids) >= 2 and fraction > 0:
            n = 1
        chosen.update(ids[:n])
    return chosen


def assign_splits(df: pd.DataFrame, seed: int, test_fraction: float = 0.15, val_fraction: float = 0.15,
                  use_locked_test: bool = True) -> pd.DataFrame:
    out = df.copy()
    out["component"] = components(out)
    locked = out.split.eq("locked_test") if (use_locked_test and "split" in out.columns) else pd.Series(False, index=out.index)
    mixed = out.groupby("component").apply(lambda g: locked[g.index].nunique() > 1, include_groups=False)
    if mixed.any():
        raise LeakageError(f"{int(mixed.sum())} leakage component(s) span the locked test and other rows; fix the "
                           "data (do not move locked-test rows)")
    maj = out.groupby("component").stance.agg(lambda s: s.value_counts().sort_index().idxmax())
    rng = np.random.default_rng(seed)
    if locked.any():
        test_comps = set(out.component[locked])
    else:
        test_comps = _stratified_pick(maj, test_fraction, rng)
    rest = maj[~maj.index.isin(test_comps)]
    val_comps = _stratified_pick(rest, val_fraction / max(1e-9, 1 - (0 if locked.any() else test_fraction)), rng)
    out["assigned_split"] = np.where(out.component.isin(test_comps), "test",
                                     np.where(out.component.isin(val_comps), "val", "train"))
    return out


def check_leakage(df: pd.DataFrame, split_col: str = "assigned_split", near_dup_threshold: float | None = 0.8) -> dict:
    """Raise LeakageError if any group key, normalised text, or near-duplicate text crosses splits."""
    report: dict[str, int] = {}
    problems = []
    norm = df.text.map(norm_tweet)
    for key, values in [(k, df[k]) for k in GROUP_KEYS if k in df.columns] + [("normalised_text", norm)]:
        per = pd.DataFrame({"v": values, "s": df[split_col]})
        per = per[per.v != ""]
        crossing = int((per.groupby("v").s.nunique() > 1).sum())
        report[f"{key}_crossing"] = crossing
        if crossing:
            problems.append(f"{crossing} {key} value(s) appear in more than one split")
    if near_dup_threshold is not None:
        toks = norm.map(token_set)
        test_idx = df.index[df[split_col] == "test"]
        other_idx = df.index[df[split_col] != "test"]
        pairs = sum(1 for i in test_idx for j in other_idx if jaccard(toks[i], toks[j]) >= near_dup_threshold)
        report["near_duplicate_pairs_test_vs_rest"] = pairs
        if pairs:
            problems.append(f"{pairs} near-duplicate text pair(s) between test and train/val")
    if problems:
        raise LeakageError("split leakage: " + "; ".join(problems))
    return report

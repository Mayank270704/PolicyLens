"""Train Indian stance baselines on ADJUDICATED HUMAN labels; select on validation only.

    python -m ml.indian_stance.train --data <adjudicated_labels.csv> --config configs/indian_stance/baseline_v1.json \
        --out-dir data/processed/indian/runs/<run_name>

Refuses: missing/blank labels, sentiment or pseudo labels, non-adjudicated rows, context-only sources,
unjustified multi-source merges, split leakage, and too few examples per class. The test split is
never passed to a model here; use ml.indian_stance.evaluate once, after selection is final.
"""
from __future__ import annotations

import argparse
import itertools
import json
import platform
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from ml.indian_stance.annotation_schema import STANCE_LABELS
from ml.indian_stance.common import git_commit, new_output_dir, sha256_file, utc_now, write_csv, write_json
from ml.indian_stance.data_loader import LabelValidationError, load_labelled
from ml.indian_stance.splits import LeakageError, assign_splits, check_leakage

# Keeps Devanagari words whole (vowel signs are not \w in Python's regex) and keeps negations:
# no stop-word list is used anywhere (the Canadian Experiment 3 lesson).
TOKEN_PATTERN = r"(?u)[\wऀ-ॣ०-ॿ]{2,}"


class TrainingRefused(RuntimeError):
    pass


def build_pipeline(model: dict, params: dict, seed: int) -> Pipeline:
    kind = model["classifier"]["type"]
    if model["features"] == "word":
        feats = TfidfVectorizer(analyzer="word", token_pattern=TOKEN_PATTERN, lowercase=True,
                                ngram_range=tuple(model["word_ngram_range"]), min_df=params["min_df"], sublinear_tf=True)
    elif model["features"] == "word_char":
        feats = FeatureUnion([
            ("word", TfidfVectorizer(analyzer="word", token_pattern=TOKEN_PATTERN, lowercase=True,
                                     ngram_range=tuple(model["word_ngram_range"]), min_df=params["min_df"], sublinear_tf=True)),
            ("char", TfidfVectorizer(analyzer="char_wb", lowercase=True, ngram_range=tuple(model["char_ngram_range"]),
                                     min_df=params["min_df"], sublinear_tf=True))])
    else:
        raise ValueError(f"unknown features {model['features']}")
    if kind == "logreg":
        clf = LogisticRegression(C=params["C"], class_weight=params["class_weight"], max_iter=5000, random_state=seed)
    elif kind == "linearsvc":
        clf = LinearSVC(C=params["C"], class_weight=params["class_weight"], max_iter=20000, random_state=seed)
    else:
        raise ValueError(f"unknown classifier {kind}")
    return Pipeline([("features", feats), ("clf", clf)])


def grid(model: dict):
    keys = list(model["grid"])
    for values in itertools.product(*(model["grid"][k] for k in keys)):
        yield dict(zip(keys, values))


def macro_f1(y_true, y_pred) -> float:
    return float(f1_score(y_true, y_pred, labels=list(STANCE_LABELS), average="macro", zero_division=0))


def run(data: Path, config_path: Path, out_dir: Path, allow_multi_source=False, merge_justification="") -> dict:
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    seed = int(cfg["seed"])
    df = load_labelled(data, allow_multi_source, merge_justification)
    s = cfg["split"]
    df = assign_splits(df, seed, s["test_fraction"], s["val_fraction"], s.get("use_locked_test_column", True))
    leak = check_leakage(df, near_dup_threshold=s.get("near_duplicate_jaccard", 0.8))
    counts = {sp: df[df.assigned_split == sp].stance.value_counts().reindex(STANCE_LABELS, fill_value=0).astype(int).to_dict()
              for sp in ("train", "val", "test")}
    floor = int(cfg.get("min_per_class_train", 5))
    short = {k: v for k, v in counts["train"].items() if v < floor}
    if short:
        raise TrainingRefused(f"too few training examples per class (min {floor}): {short}")
    if min(counts["val"].values()) == 0:
        raise TrainingRefused(f"validation split lacks a class: {counts['val']}")
    train, val = df[df.assigned_split == "train"], df[df.assigned_split == "val"]
    results, best = [], None
    for model in cfg["models"]:
        for params in grid(model):
            pipe = build_pipeline(model, params, seed).fit(train.text, train.stance)
            score = macro_f1(val.stance, pipe.predict(val.text))
            per_source = {src: round(macro_f1(g.stance, pipe.predict(g.text)), 4) for src, g in val.groupby("source")}
            results.append({"model": model["name"], "params": params, "val_macro_f1": round(score, 4),
                            "val_macro_f1_by_source": per_source})
            if best is None or score > best[0]:
                best = (score, model, params, pipe)
    score, model, params, pipe = best
    if cfg.get("refit_on_train_plus_val"):
        tv = df[df.assigned_split != "test"]
        pipe = build_pipeline(model, params, seed).fit(tv.text, tv.stance)
    out_dir = new_output_dir(out_dir)
    joblib.dump(pipe, out_dir / "model.joblib")
    write_csv(out_dir / "splits.csv", df[["item_id", "source", "component", "assigned_split"]].to_dict("records"),
              ["item_id", "source", "component", "assigned_split"])
    write_json(out_dir / "selection_results.json", results)
    manifest = {"created_utc": utc_now(), "code_git_commit": git_commit(),
                "data": {"path": Path(data).as_posix(), "sha256": sha256_file(data), "rows": len(df),
                         "sources": sorted(df.source.unique()), "merge_justification": merge_justification or None},
                "config": {"path": Path(config_path).as_posix(), "sha256": sha256_file(config_path), "content": cfg},
                "seed": seed, "label_counts_by_split": counts, "leakage_check": leak,
                "selected": {"model": model["name"], "params": params, "val_macro_f1": round(score, 4),
                             "refit_on_train_plus_val": bool(cfg.get("refit_on_train_plus_val"))},
                "test_evaluations_performed": 0,
                "environment": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                                "numpy": np.__version__, "pandas": pd.__version__},
                "model_sha256": sha256_file(out_dir / "model.joblib")}
    write_json(out_dir / "run_manifest.json", manifest)
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--allow-multi-source", action="store_true")
    ap.add_argument("--merge-justification", default="")
    a = ap.parse_args(argv)
    try:
        m = run(Path(a.data), Path(a.config), Path(a.out_dir), a.allow_multi_source, a.merge_justification)
    except (LabelValidationError, LeakageError, TrainingRefused, FileExistsError) as e:
        print(f"[REFUSED] {e}", file=sys.stderr)
        return 2
    print(json.dumps({k: m[k] for k in ("selected", "label_counts_by_split", "leakage_check")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())

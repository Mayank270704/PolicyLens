"""Single-use held-out TEST evaluation of a trained run (after model selection is final).

    python -m ml.indian_stance.evaluate --run-dir data/processed/indian/runs/<run_name> --data <same_labels.csv>

Refuses if the data file differs from the one the run was trained on, or if the test split was
already evaluated. Writes metrics and an error-analysis file (IDs and labels only; no text).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_recall_fscore_support

from ml.indian_stance.annotation_schema import STANCE_LABELS
from ml.indian_stance.common import sha256_file, utc_now, write_csv, write_json
from ml.indian_stance.data_loader import LabelValidationError, load_labelled


class EvaluationRefused(RuntimeError):
    pass


def metrics(y_true, y_pred) -> dict:
    labels = list(STANCE_LABELS)
    p, r, f, sup = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    return {"n": int(len(y_true)), "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "macro_f1": round(float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)), 4),
            "weighted_f1": round(float(f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)), 4),
            "per_class": {lab: {"precision": round(float(p[i]), 4), "recall": round(float(r[i]), 4),
                                "f1": round(float(f[i]), 4), "support": int(sup[i])} for i, lab in enumerate(labels)},
            "confusion_matrix": {"labels_order": labels, "rows_true_cols_pred": confusion_matrix(y_true, y_pred, labels=labels).tolist()},
            "classification_report": classification_report(y_true, y_pred, labels=labels, zero_division=0)}


def run(run_dir: Path, data: Path, allow_multi_source=False, merge_justification="") -> dict:
    run_dir = Path(run_dir)
    man = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    out = run_dir / "test_evaluation"
    if out.exists():
        raise EvaluationRefused("test split already evaluated for this run; the test set is single-use")
    if sha256_file(data) != man["data"]["sha256"]:
        raise EvaluationRefused("data file differs from the one used for training")
    if sha256_file(run_dir / "model.joblib") != man["model_sha256"]:
        raise EvaluationRefused("model.joblib does not match its manifest hash")
    df = load_labelled(data, allow_multi_source, merge_justification).set_index("item_id")
    splits = pd.read_csv(run_dir / "splits.csv", dtype=str, keep_default_na=False)
    test_ids = splits.item_id[splits.assigned_split == "test"].tolist()
    test = df.loc[test_ids]
    pred = joblib.load(run_dir / "model.joblib").predict(test.text)
    res = {"created_utc": utc_now(), "overall": metrics(test.stance, pred),
           "by_source": {s: metrics(test.stance[test.source == s], pred[(test.source == s).values])
                         for s in sorted(test.source.unique())}}
    out.mkdir()
    write_json(out / "test_metrics.json", res)
    errs = [{"item_id": i, "source": s, "true_stance": t, "predicted_stance": p, "unclear_reason": u}
            for i, s, t, p, u in zip(test.index, test.source, test.stance, pred, test.unclear_reason) if t != p]
    write_csv(out / "error_analysis.csv", errs, ["item_id", "source", "true_stance", "predicted_stance", "unclear_reason"])
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--allow-multi-source", action="store_true")
    ap.add_argument("--merge-justification", default="")
    a = ap.parse_args(argv)
    try:
        r = run(Path(a.run_dir), Path(a.data), a.allow_multi_source, a.merge_justification)
    except (EvaluationRefused, LabelValidationError, FileNotFoundError) as e:
        print(f"[REFUSED] {e}", file=sys.stderr)
        return 2
    print(r["overall"]["classification_report"])
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())

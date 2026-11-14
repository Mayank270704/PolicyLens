"""Experiment 2 — TF-IDF + LinearSVC four-class stance baseline.

See docs/experiments/STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md (Experiment 2).

- Fits TF-IDF and LinearSVC on train.csv only; selects hyperparameters by
  validation macro-F1.
- The test split was already scored by Experiment 1 and is treated as
  development-exposed: this module never predicts on it (it only records
  its hash for provenance).
- LinearSVC has no calibrated probabilities. Predictions expose raw
  per-class decision scores, which are NOT probabilities or confidences.
- Comparison with Experiment 1 uses only its train/val metrics.

Run directly:
    python ml/stance_classification/tfidf_linearsvc.py
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
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.svm import LinearSVC

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ml.stance_classification import tfidf_logreg as lr
from scripts.annotation import schema as ann_schema

EXPERIMENT_NAME = "exp2_tfidf_linearsvc"
MODEL_VERSION = "tfidf_linearsvc_v1"
LABELS = lr.LABELS
LABEL_TO_INDEX = lr.LABEL_TO_INDEX
SEED = lr.SEED
preprocess = lr.preprocess
load_split = lr.load_split
compute_metrics = lr.compute_metrics
StanceModelError = lr.StanceModelError

DEFAULT_SPLITS_DIR = lr.DEFAULT_SPLITS_DIR
DEFAULT_ARTIFACT_DIR = ann_schema.REPO_ROOT / "models" / "stance" / MODEL_VERSION
DEFAULT_LOGREG_REPORT = lr.DEFAULT_ARTIFACT_DIR / lr.EVAL_REPORT_FILE

VECTORIZER_FILE = "tfidf_vectorizer.joblib"
MODEL_FILE = "linearsvc_model.joblib"
LABEL_MAPPING_FILE = "label_mapping.json"
CONFIG_FILE = "config.json"
METADATA_FILE = "training_metadata.json"
EVAL_REPORT_FILE = "evaluation_report.json"

# Ordered simplest-first (stronger regularization, smaller feature space,
# balanced weighting) so validation-F1 ties resolve conservatively.
PARAM_GRID = {
    "C": [0.01, 0.03, 0.1, 0.3, 1.0, 3.0],
    "ngram_range": [(1, 1), (1, 2)],
    "min_df": [2, 1],
    "class_weight": ["balanced", None],
}

# Identical to Experiment 1 so the comparison isolates the classifier.
FIXED_VECTORIZER_PARAMS = {**lr.FIXED_VECTORIZER_PARAMS, "sublinear_tf": False}
FIXED_CLASSIFIER_PARAMS = {"loss": "squared_hinge", "dual": "auto", "max_iter": 20000}


class TfidfLinearSVCStanceModel:
    """Fitted vectorizer + LinearSVC with the fixed four-label mapping."""

    def __init__(self, vectorizer: TfidfVectorizer, classifier: LinearSVC, params: dict):
        self.vectorizer = vectorizer
        self.classifier = classifier
        self.params = params
        if list(classifier.classes_) != list(range(len(LABELS))):
            raise StanceModelError(
                f"Classifier classes_ {list(classifier.classes_)} do not match the fixed "
                f"four-label index mapping {list(range(len(LABELS)))}"
            )

    @classmethod
    def fit(cls, texts: list[str], labels: list[str], params: dict, seed: int = SEED) -> "TfidfLinearSVCStanceModel":
        unknown = sorted(set(labels) - set(LABELS))
        if unknown:
            raise StanceModelError(f"Unknown training label(s): {unknown}")
        missing = [label for label in LABELS if label not in set(labels)]
        if missing:
            raise StanceModelError(f"Training data is missing class(es) {missing}; all four are required")
        y = np.array([LABEL_TO_INDEX[label] for label in labels])
        vectorizer = TfidfVectorizer(
            ngram_range=tuple(params["ngram_range"]), min_df=params["min_df"], **FIXED_VECTORIZER_PARAMS
        )
        X = vectorizer.fit_transform([preprocess(t) for t in texts])
        classifier = LinearSVC(
            C=params["C"], class_weight=params["class_weight"], random_state=seed, **FIXED_CLASSIFIER_PARAMS
        )
        classifier.fit(X, y)
        return cls(vectorizer, classifier, params)

    def _transform(self, texts: list[str]):
        if not isinstance(texts, (list, tuple)):
            raise ValueError("texts must be a list of strings")
        return self.vectorizer.transform([preprocess(t) for t in texts])

    def predict_indices(self, texts: list[str]) -> np.ndarray:
        if len(texts) == 0:
            return np.array([], dtype=int)
        return self.classifier.predict(self._transform(texts))

    def predict(self, texts: list[str]) -> list[str]:
        return [LABELS[i] for i in self.predict_indices(texts)]

    def decision_scores(self, texts: list[str]) -> list[dict[str, float]]:
        """Raw one-vs-rest margins per label. Not probabilities."""
        if len(texts) == 0:
            return []
        scores = self.classifier.decision_function(self._transform(texts))
        return [{LABELS[j]: float(row[j]) for j in range(len(LABELS))} for row in scores]

    def save(self, artifact_dir: Path, config: dict, metadata: dict) -> dict[str, str]:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.vectorizer, artifact_dir / VECTORIZER_FILE)
        joblib.dump(self.classifier, artifact_dir / MODEL_FILE)
        _write_json(artifact_dir / LABEL_MAPPING_FILE, {
            "labels": list(LABELS),
            "label_to_index": LABEL_TO_INDEX,
            "index_to_label": {str(i): label for i, label in enumerate(LABELS)},
        })
        _write_json(artifact_dir / CONFIG_FILE, config)
        hashes = {
            name: ann_schema.sha256_file(artifact_dir / name)
            for name in (VECTORIZER_FILE, MODEL_FILE, LABEL_MAPPING_FILE, CONFIG_FILE)
        }
        _write_json(artifact_dir / METADATA_FILE, {**metadata, "artifact_sha256": hashes})
        return hashes

    @classmethod
    def load(cls, artifact_dir: Path) -> "TfidfLinearSVCStanceModel":
        """Loads only artifacts whose SHA-256 matches training_metadata.json.
        joblib files are pickles: only load artifact directories you produced."""
        artifact_dir = Path(artifact_dir)
        metadata_path = artifact_dir / METADATA_FILE
        if not metadata_path.exists():
            raise StanceModelError(f"No {METADATA_FILE} in {artifact_dir}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        for name, expected in metadata.get("artifact_sha256", {}).items():
            path = artifact_dir / name
            if not path.exists():
                raise StanceModelError(f"Missing artifact {path}")
            if ann_schema.sha256_file(path) != expected:
                raise StanceModelError(f"SHA-256 mismatch for {path}; refusing to load")
        mapping = json.loads((artifact_dir / LABEL_MAPPING_FILE).read_text(encoding="utf-8"))
        if mapping.get("labels") != list(LABELS):
            raise StanceModelError(f"Saved label mapping {mapping.get('labels')} != expected {list(LABELS)}")
        config = json.loads((artifact_dir / CONFIG_FILE).read_text(encoding="utf-8"))
        vectorizer = joblib.load(artifact_dir / VECTORIZER_FILE)
        classifier = joblib.load(artifact_dir / MODEL_FILE)
        return cls(vectorizer, classifier, config["selected_hyperparameters"])

    def top_terms(self, n: int = 15) -> dict[str, list[tuple[str, float]]]:
        vocab = np.array(self.vectorizer.get_feature_names_out())
        out = {}
        for i, label in enumerate(LABELS):
            coefs = self.classifier.coef_[i]
            top = np.argsort(coefs)[::-1][:n]
            out[label] = [(str(vocab[j]), round(float(coefs[j]), 4)) for j in top]
        return out


def _write_json(path: Path, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def _jsonable_params(params: dict) -> dict:
    return {**params, "ngram_range": list(params["ngram_range"])}


def iter_param_grid(grid: dict = PARAM_GRID):
    keys = list(grid)
    for values in itertools.product(*(grid[k] for k in keys)):
        yield dict(zip(keys, values))


def select_hyperparameters(train, val, grid: dict = PARAM_GRID, seed: int = SEED):
    """Uses train and val only. Returns (best_params, all_results)."""
    results = []
    best = None
    for params in iter_param_grid(grid):
        model = TfidfLinearSVCStanceModel.fit(train.texts, train.labels, params, seed=seed)
        val_pred = model.predict_indices(val.texts)
        macro = f1_score(val.y, val_pred, labels=list(range(len(LABELS))), average="macro", zero_division=0)
        results.append({
            "params": _jsonable_params(params),
            "val_macro_f1": round(float(macro), 4),
            "val_accuracy": round(float(accuracy_score(val.y, val_pred)), 4),
            "n_features": len(model.vectorizer.vocabulary_),
        })
        if best is None or macro > best[0]:
            best = (macro, params)
    return best[1], results


def compare_with_logreg(svc_train: dict, svc_val: dict, logreg_report_path: Path) -> dict:
    """Train/val-only comparison. Experiment 1's test metrics are never read."""
    logreg_report_path = Path(logreg_report_path)
    if not logreg_report_path.exists():
        return {"status": "logreg_report_not_found", "path": str(logreg_report_path)}
    report = json.loads(logreg_report_path.read_text(encoding="utf-8"))
    lr_train, lr_val = report["train_metrics"], report["val_metrics"]

    def summary(train_m, val_m):
        return {
            "train_macro_f1": train_m["macro_f1"],
            "val_macro_f1": val_m["macro_f1"],
            "val_accuracy": val_m["accuracy"],
            "overfit_gap_macro_f1": round(train_m["macro_f1"] - val_m["macro_f1"], 4),
            "val_per_class": {
                label: {"recall": val_m["per_class"][label]["recall"], "f1": val_m["per_class"][label]["f1"]}
                for label in LABELS
            },
            "val_confusion_matrix": val_m["confusion_matrix"],
        }

    return {
        "status": "ok",
        "basis": "train and validation metrics only; the development-exposed test split is not used",
        "logreg_selected_hyperparameters": report.get("selected_hyperparameters"),
        "logreg": summary(lr_train, lr_val),
        "linearsvc": summary(svc_train, svc_val),
        "val_macro_f1_difference_svc_minus_logreg": round(svc_val["macro_f1"] - lr_val["macro_f1"], 4),
        "val_n": svc_val["n"],
    }


def run(
    splits_dir: Path = DEFAULT_SPLITS_DIR,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    logreg_report_path: Path = DEFAULT_LOGREG_REPORT,
    seed: int = SEED,
    grid: dict = PARAM_GRID,
) -> dict:
    splits_dir, artifact_dir = Path(splits_dir), Path(artifact_dir)
    if (artifact_dir / METADATA_FILE).exists():
        raise StanceModelError(
            f"{artifact_dir} already holds a trained model. Refusing to overwrite; "
            "use a new model version directory for a new experiment."
        )
    manifest_path = splits_dir / "split_manifest.json"
    if not manifest_path.exists():
        raise StanceModelError(f"No split manifest at {manifest_path}; run dataset_prep.py first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    train = load_split(splits_dir / "train.csv")
    val = load_split(splits_dir / "val.csv")

    best_params, tuning_results = select_hyperparameters(train, val, grid=grid, seed=seed)
    model = TfidfLinearSVCStanceModel.fit(train.texts, train.labels, best_params, seed=seed)
    train_metrics = compute_metrics(train.y, model.predict_indices(train.texts))
    val_pred = model.predict_indices(val.texts)
    val_metrics = compute_metrics(val.y, val_pred)
    val_scores = model.decision_scores(val.texts)

    val_misclassified = [
        {
            "comment_id": val.comment_ids[i],
            "comment_text": val.raw_rows[i]["comment_text"],
            "true_label": LABELS[t],
            "predicted_label": LABELS[p],
            "decision_scores_not_probabilities": {k: round(v, 4) for k, v in val_scores[i].items()},
            "annotation_confidence": val.raw_rows[i].get("annotation_confidence", ""),
        }
        for i, (t, p) in enumerate(zip(val.y, val_pred))
        if t != p
    ]

    test_path = splits_dir / "test.csv"
    selected = _jsonable_params(best_params)
    config = {
        "experiment": EXPERIMENT_NAME,
        "model_version": MODEL_VERSION,
        "seed": seed,
        "labels": list(LABELS),
        "text_field": "normalized_text",
        "preprocessing": "dataset_prep.normalize_text (shared with Experiment 1), then TfidfVectorizer lowercase/accents/stopwords",
        "selected_hyperparameters": selected,
        "fixed_vectorizer_params": FIXED_VECTORIZER_PARAMS,
        "fixed_classifier_params": FIXED_CLASSIFIER_PARAMS,
        "param_grid": {k: [list(v) if isinstance(v, tuple) else v for v in vals] for k, vals in grid.items()},
        "selection_criterion": "validation macro-F1 (ties -> first in simplest-first grid order)",
        "vectorizer_fit_on": "train only",
        "classifier_fit_on": "train only",
        "probability_output": "none -- LinearSVC decision scores are uncalibrated margins, not probabilities",
    }
    metadata = {
        "generated_utc": ann_schema.utcnow_iso(),
        "split_manifest_source_sha256": manifest.get("source_sha256"),
        "split_manifest_sha256": ann_schema.sha256_file(manifest_path),
        "split_file_sha256": {
            name: ann_schema.sha256_file(splits_dir / f"{name}.csv")
            for name in ("train", "val", "test") if (splits_dir / f"{name}.csv").exists()
        },
        "n_train": len(train.labels),
        "n_val": len(val.labels),
        "class_distribution": {
            "train": {label: train.labels.count(label) for label in LABELS},
            "val": {label: val.labels.count(label) for label in LABELS},
        },
        "n_features": len(model.vectorizer.vocabulary_),
        "test_set_status": "development-exposed by Experiment 1; not scored by this experiment",
        "test_evaluations_performed": 0,
        "test_split_present": test_path.exists(),
        "no_pseudo_labels_used": True,
        "no_oversampling": True,
        "environment": {
            "python": platform.python_version(),
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
            "joblib": joblib.__version__,
        },
        "gold_standard_claim": "NOT MADE -- trained on a single-annotator provisional dataset.",
    }
    hashes = model.save(artifact_dir, config, metadata)

    report = {
        "experiment": EXPERIMENT_NAME,
        "model_version": MODEL_VERSION,
        "selected_hyperparameters": selected,
        "tuning_results": tuning_results,
        "train_metrics": train_metrics,
        "val_metrics": val_metrics,
        "val_misclassified": val_misclassified,
        "comparison_with_logreg": compare_with_logreg(train_metrics, val_metrics, logreg_report_path),
        "top_terms_per_class": model.top_terms(),
        "test_set_status": metadata["test_set_status"],
        "artifact_sha256": hashes,
    }
    _write_json(artifact_dir / EVAL_REPORT_FILE, report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Experiment 2: TF-IDF + LinearSVC stance baseline.")
    parser.add_argument("--splits-dir", type=Path, default=DEFAULT_SPLITS_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--logreg-report", type=Path, default=DEFAULT_LOGREG_REPORT)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args(argv)

    try:
        report = run(args.splits_dir, args.artifact_dir, args.logreg_report, seed=args.seed)
    except StanceModelError as e:
        print(f"Experiment 2 refused:\n{e}")
        return 1

    print(f"Selected hyperparameters: {report['selected_hyperparameters']}")
    print(lr._format_metrics("TRAIN", report["train_metrics"]))
    print(lr._format_metrics("VAL", report["val_metrics"]))
    cm = report["val_metrics"]["confusion_matrix"]
    print(f"Validation confusion matrix (rows=true, cols=pred, order={cm['labels_order']}):")
    for label, row in zip(cm["labels_order"], cm["rows_true_cols_pred"]):
        print(f"  {label:<8} {row}")
    print(f"Validation misclassified: {len(report['val_misclassified'])}")
    print("Test split: not scored (development-exposed).")
    print(f"Artifacts: {args.artifact_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

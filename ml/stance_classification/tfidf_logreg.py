"""Experiment 1 — TF-IDF + Logistic Regression four-class stance baseline.

See docs/experiments/STANCE_CLASSIFICATION_EXPERIMENT_PLAN.md (Experiment 1).

- Trains on data/processed/stance_classification_splits/train.csv only; the
  TF-IDF vectorizer is fit on training text only (never val/test).
- Hyperparameters are selected by validation macro-F1; the test split is
  read and scored exactly once, after selection is final.
- Refuses to overwrite an existing artifact directory, so the test set
  cannot be silently re-scored after looking at it.

Run directly:
    python ml/stance_classification/tfidf_logreg.py
"""
from __future__ import annotations

import argparse
import itertools
import json
import platform
import sys
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ml.stance_classification import dataset_prep as dp
from scripts.annotation import schema as ann_schema

EXPERIMENT_NAME = "exp1_tfidf_logreg"
MODEL_VERSION = "tfidf_logreg_v1"
LABELS: tuple[str, ...] = tuple(ann_schema.STANCE_LABELS)
LABEL_TO_INDEX = {label: i for i, label in enumerate(LABELS)}
SEED = 20261108

DEFAULT_SPLITS_DIR = dp.DEFAULT_OUTPUT_DIR
DEFAULT_ARTIFACT_DIR = ann_schema.REPO_ROOT / "models" / "stance" / MODEL_VERSION

VECTORIZER_FILE = "tfidf_vectorizer.joblib"
MODEL_FILE = "logreg_model.joblib"
LABEL_MAPPING_FILE = "label_mapping.json"
CONFIG_FILE = "config.json"
METADATA_FILE = "training_metadata.json"
EVAL_REPORT_FILE = "evaluation_report.json"

# Ordered simplest-first so ties on validation macro-F1 resolve to the
# more regularized / smaller-feature-space configuration.
PARAM_GRID = {
    "C": [0.1, 0.3, 1.0, 3.0, 10.0, 30.0],
    "ngram_range": [(1, 1), (1, 2)],
    "min_df": [2, 1],
    "sublinear_tf": [True, False],
}

FIXED_VECTORIZER_PARAMS = {"lowercase": True, "stop_words": "english", "strip_accents": "unicode"}
FIXED_CLASSIFIER_PARAMS = {"class_weight": "balanced", "max_iter": 5000, "solver": "lbfgs"}


class StanceModelError(RuntimeError):
    pass


def preprocess(text) -> str:
    """Single preprocessing path shared by training and inference."""
    if text is None or not isinstance(text, str):
        raise ValueError(f"comment text must be a non-empty string, got {type(text).__name__}")
    normalized = dp.normalize_text(text)
    if not normalized:
        raise ValueError("comment text is empty or whitespace-only")
    return normalized


@dataclass
class SplitData:
    comment_ids: list[str]
    texts: list[str]
    labels: list[str]
    raw_rows: list[dict]

    @property
    def y(self) -> np.ndarray:
        return np.array([LABEL_TO_INDEX[label] for label in self.labels])


def load_split(path: Path) -> SplitData:
    path = Path(path)
    if not path.exists():
        raise StanceModelError(f"Split file not found: {path}")
    rows = ann_schema.read_rows(path)
    if not rows:
        raise StanceModelError(f"Split file is empty: {path}")
    ids, texts, labels = [], [], []
    for row in rows:
        label = (row.get("annotator_label") or "").strip()
        if label not in LABEL_TO_INDEX:
            raise StanceModelError(
                f"{path.name}: invalid label {label!r} for comment_id={row.get('comment_id')}; "
                f"expected one of {list(LABELS)}"
            )
        if (row.get("exclusion_code") or "").strip():
            raise StanceModelError(f"{path.name}: excluded row {row.get('comment_id')} in a classification split")
        normalized = row.get("normalized_text")
        if normalized != dp.normalize_text(row.get("comment_text", "")):
            raise StanceModelError(
                f"{path.name}: normalized_text for {row.get('comment_id')} does not match "
                "dataset_prep.normalize_text(comment_text) -- preprocessing drift"
            )
        ids.append(row["comment_id"])
        texts.append(preprocess(normalized))
        labels.append(label)
    return SplitData(comment_ids=ids, texts=texts, labels=labels, raw_rows=rows)


class TfidfLogRegStanceModel:
    """Fitted vectorizer + classifier with a fixed four-label mapping."""

    def __init__(self, vectorizer: TfidfVectorizer, classifier: LogisticRegression, params: dict):
        self.vectorizer = vectorizer
        self.classifier = classifier
        self.params = params
        self._check_label_alignment()

    @classmethod
    def fit(cls, texts: list[str], labels: list[str], params: dict, seed: int = SEED) -> "TfidfLogRegStanceModel":
        missing = [label for label in LABELS if label not in set(labels)]
        if missing:
            raise StanceModelError(f"Training data is missing class(es) {missing}; all four are required")
        unknown = sorted(set(labels) - set(LABELS))
        if unknown:
            raise StanceModelError(f"Unknown training label(s): {unknown}")
        y = np.array([LABEL_TO_INDEX[label] for label in labels])
        vectorizer = TfidfVectorizer(
            ngram_range=tuple(params["ngram_range"]),
            min_df=params["min_df"],
            sublinear_tf=params["sublinear_tf"],
            **FIXED_VECTORIZER_PARAMS,
        )
        X = vectorizer.fit_transform([preprocess(t) for t in texts])
        classifier = LogisticRegression(C=params["C"], random_state=seed, **FIXED_CLASSIFIER_PARAMS)
        classifier.fit(X, y)
        return cls(vectorizer, classifier, params)

    def _check_label_alignment(self) -> None:
        if list(self.classifier.classes_) != list(range(len(LABELS))):
            raise StanceModelError(
                f"Classifier classes_ {list(self.classifier.classes_)} do not match the fixed "
                f"four-label index mapping {list(range(len(LABELS)))}"
            )

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

    def predict_proba(self, texts: list[str]) -> list[dict[str, float]]:
        if len(texts) == 0:
            return []
        probs = self.classifier.predict_proba(self._transform(texts))
        return [{LABELS[j]: float(row[j]) for j in range(len(LABELS))} for row in probs]

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
    def load(cls, artifact_dir: Path) -> "TfidfLogRegStanceModel":
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


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    indices = list(range(len(LABELS)))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=indices, zero_division=0
    )
    return {
        "n": int(len(y_true)),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, labels=indices, average="macro", zero_division=0)), 4),
        "weighted_f1": round(float(f1_score(y_true, y_pred, labels=indices, average="weighted", zero_division=0)), 4),
        "per_class": {
            label: {
                "precision": round(float(precision[i]), 4),
                "recall": round(float(recall[i]), 4),
                "f1": round(float(f1[i]), 4),
                "support": int(support[i]),
            }
            for i, label in enumerate(LABELS)
        },
        "confusion_matrix": {
            "labels_order": list(LABELS),
            "rows_true_cols_pred": confusion_matrix(y_true, y_pred, labels=indices).tolist(),
        },
    }


def iter_param_grid(grid: dict = PARAM_GRID):
    keys = list(grid)
    for values in itertools.product(*(grid[k] for k in keys)):
        yield dict(zip(keys, values))


def select_hyperparameters(train: SplitData, val: SplitData, grid: dict = PARAM_GRID, seed: int = SEED):
    """Uses train and val only. Returns (best_params, all_results)."""
    results = []
    best = None
    for params in iter_param_grid(grid):
        model = TfidfLogRegStanceModel.fit(train.texts, train.labels, params, seed=seed)
        val_pred = model.predict_indices(val.texts)
        macro = f1_score(val.y, val_pred, labels=list(range(len(LABELS))), average="macro", zero_division=0)
        results.append({
            "params": {**params, "ngram_range": list(params["ngram_range"])},
            "val_macro_f1": round(float(macro), 4),
            "val_accuracy": round(float(accuracy_score(val.y, val_pred)), 4),
            "n_features": len(model.vectorizer.vocabulary_),
        })
        if best is None or macro > best[0]:
            best = (macro, params)
    return best[1], results


def _distribution(labels: list[str]) -> dict[str, int]:
    return {label: labels.count(label) for label in LABELS}


def run(
    splits_dir: Path = DEFAULT_SPLITS_DIR,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    seed: int = SEED,
    grid: dict = PARAM_GRID,
) -> dict:
    splits_dir, artifact_dir = Path(splits_dir), Path(artifact_dir)
    if (artifact_dir / EVAL_REPORT_FILE).exists():
        raise StanceModelError(
            f"{artifact_dir} already holds an evaluated model. Refusing to retrain and re-score the "
            "test set; use a new model version directory for a new experiment."
        )

    manifest_path = splits_dir / "split_manifest.json"
    if not manifest_path.exists():
        raise StanceModelError(f"No split manifest at {manifest_path}; run dataset_prep.py first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    train = load_split(splits_dir / "train.csv")
    val = load_split(splits_dir / "val.csv")

    best_params, tuning_results = select_hyperparameters(train, val, grid=grid, seed=seed)
    model = TfidfLogRegStanceModel.fit(train.texts, train.labels, best_params, seed=seed)
    train_metrics = compute_metrics(train.y, model.predict_indices(train.texts))
    val_metrics = compute_metrics(val.y, model.predict_indices(val.texts))

    # Model selection is final from here on; the test split is read and scored once.
    test = load_split(splits_dir / "test.csv")
    test_pred = model.predict_indices(test.texts)
    test_proba = model.predict_proba(test.texts)
    test_metrics = compute_metrics(test.y, test_pred)

    misclassified = []
    for i, (true_idx, pred_idx) in enumerate(zip(test.y, test_pred)):
        if true_idx != pred_idx:
            misclassified.append({
                "comment_id": test.comment_ids[i],
                "comment_text": test.raw_rows[i]["comment_text"],
                "true_label": LABELS[true_idx],
                "predicted_label": LABELS[pred_idx],
                "predicted_probabilities": {k: round(v, 4) for k, v in test_proba[i].items()},
                "annotation_confidence": test.raw_rows[i].get("annotation_confidence", ""),
            })

    selected = {**best_params, "ngram_range": list(best_params["ngram_range"])}
    config = {
        "experiment": EXPERIMENT_NAME,
        "model_version": MODEL_VERSION,
        "seed": seed,
        "labels": list(LABELS),
        "text_field": "normalized_text",
        "preprocessing": "dataset_prep.normalize_text (whitespace collapse + trim), then TfidfVectorizer lowercase/accents/stopwords",
        "selected_hyperparameters": selected,
        "fixed_vectorizer_params": FIXED_VECTORIZER_PARAMS,
        "fixed_classifier_params": FIXED_CLASSIFIER_PARAMS,
        "param_grid": {k: [list(v) if isinstance(v, tuple) else v for v in vals] for k, vals in grid.items()},
        "selection_criterion": "validation macro-F1 (ties -> first in simplest-first grid order)",
        "vectorizer_fit_on": "train only",
        "classifier_fit_on": "train only",
    }
    metadata = {
        "generated_utc": ann_schema.utcnow_iso(),
        "split_manifest_source_sha256": manifest.get("source_sha256"),
        "split_manifest_sha256": ann_schema.sha256_file(manifest_path),
        "split_file_sha256": {
            name: ann_schema.sha256_file(splits_dir / f"{name}.csv") for name in ("train", "val", "test")
        },
        "n_train": len(train.labels), "n_val": len(val.labels), "n_test": len(test.labels),
        "class_distribution": {
            "train": _distribution(train.labels), "val": _distribution(val.labels), "test": _distribution(test.labels),
        },
        "n_features": len(model.vectorizer.vocabulary_),
        "test_evaluations_performed": 1,
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
        "test_metrics": test_metrics,
        "test_class_distribution": _distribution(test.labels),
        "test_misclassified": misclassified,
        "top_terms_per_class": model.top_terms(),
        "artifact_sha256": hashes,
    }
    _write_json(artifact_dir / EVAL_REPORT_FILE, report)
    return report


def _format_metrics(name: str, m: dict) -> str:
    lines = [f"{name}: n={m['n']} accuracy={m['accuracy']} macro_f1={m['macro_f1']} weighted_f1={m['weighted_f1']}"]
    for label, pc in m["per_class"].items():
        lines.append(f"  {label:<8} P={pc['precision']:.4f} R={pc['recall']:.4f} F1={pc['f1']:.4f} support={pc['support']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Experiment 1: TF-IDF + Logistic Regression stance baseline.")
    parser.add_argument("--splits-dir", type=Path, default=DEFAULT_SPLITS_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args(argv)

    try:
        report = run(args.splits_dir, args.artifact_dir, seed=args.seed)
    except StanceModelError as e:
        print(f"Experiment 1 refused:\n{e}")
        return 1

    print(f"Selected hyperparameters: {report['selected_hyperparameters']}")
    for key, name in (("train_metrics", "TRAIN"), ("val_metrics", "VAL"), ("test_metrics", "TEST")):
        print(_format_metrics(name, report[key]))
    cm = report["test_metrics"]["confusion_matrix"]
    print(f"Test confusion matrix (rows=true, cols=pred, order={cm['labels_order']}):")
    for label, row in zip(cm["labels_order"], cm["rows_true_cols_pred"]):
        print(f"  {label:<8} {row}")
    print(f"Misclassified test examples: {len(report['test_misclassified'])}")
    print(f"Artifacts: {args.artifact_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

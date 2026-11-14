"""Experiment 3 — negation-aware TF-IDF + {Logistic Regression, LinearSVC}.

Experiments 1-2 used sklearn's English stopword list, which deletes
negation/contrast words (not, no, never, against, but, ...), and the
default tokenizer, which turns "can't" into "can" (itself a stopword) and
"don't" into "don". This experiment changes only the text-to-token step:

- `negation_preprocessor` lowercases, strips accents, unifies apostrophes
  and expands n't contractions ("can't" -> "cannot", "won't" -> "will not",
  "don't" -> "do not").
- `STOP_WORDS` is sklearn's list minus `PRESERVED_TERMS`.

Hyperparameter grids are reused unchanged from Experiments 1 and 2, so any
difference is attributable to preprocessing. Training uses train.csv only,
selection uses val.csv only; the development-exposed test split is never
loaded.

Run directly:
    python ml/stance_classification/negation_tfidf.py
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import sys
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer, strip_accents_unicode
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.svm import LinearSVC

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ml.stance_classification import tfidf_linearsvc as svc
from ml.stance_classification import tfidf_logreg as lr
from scripts.annotation import schema as ann_schema

EXPERIMENT_NAME = "exp3_negation_tfidf"
MODEL_VERSION = "negation_tfidf_v1"
LABELS = lr.LABELS
LABEL_TO_INDEX = lr.LABEL_TO_INDEX
SEED = lr.SEED
StanceModelError = lr.StanceModelError
compute_metrics = lr.compute_metrics
load_split = lr.load_split

DEFAULT_SPLITS_DIR = lr.DEFAULT_SPLITS_DIR
DEFAULT_ARTIFACT_DIR = ann_schema.REPO_ROOT / "models" / "stance" / MODEL_VERSION
PREVIOUS_REPORTS = {
    "exp1_logreg": lr.DEFAULT_ARTIFACT_DIR / lr.EVAL_REPORT_FILE,
    "exp2_linearsvc": svc.DEFAULT_ARTIFACT_DIR / svc.EVAL_REPORT_FILE,
}

PRESERVED_TERMS = frozenset({
    "not", "no", "nor", "never", "against", "without", "but", "however", "although",
    "cannot", "none", "nothing", "neither", "nobody", "nowhere", "though", "yet", "except",
})
STOP_WORDS = sorted(ENGLISH_STOP_WORDS - PRESERVED_TERMS)

_APOSTROPHES = re.compile(r"[’‘`´]")
_CONTRACTIONS = [
    (re.compile(r"\bcan't\b"), "cannot"),
    (re.compile(r"\bwon't\b"), "will not"),
    (re.compile(r"\bshan't\b"), "shall not"),
    (re.compile(r"\b(\w+)n't\b"), r"\1 not"),
]

CLASSIFIERS = ("logreg", "linearsvc")
PARAM_GRIDS = {"logreg": lr.PARAM_GRID, "linearsvc": svc.PARAM_GRID}
# Each classifier's hyperparameters as selected in Experiments 1 and 2.
MATCHED_CONFIGS = {
    "logreg": {"C": 3.0, "ngram_range": (1, 2), "min_df": 2, "sublinear_tf": False},
    "linearsvc": {"C": 0.3, "ngram_range": (1, 2), "min_df": 2, "class_weight": None},
}

VECTORIZER_FILE = "tfidf_vectorizer.joblib"
MODEL_FILE = "model.joblib"
LABEL_MAPPING_FILE = "label_mapping.json"
CONFIG_FILE = "config.json"
METADATA_FILE = "training_metadata.json"
EVAL_REPORT_FILE = "evaluation_report.json"


def negation_preprocessor(text: str) -> str:
    """Runs inside the vectorizer for both fit and transform."""
    text = strip_accents_unicode(text.lower())
    text = _APOSTROPHES.sub("'", text)
    for pattern, replacement in _CONTRACTIONS:
        text = pattern.sub(replacement, text)
    return text


def build_vectorizer(params: dict) -> TfidfVectorizer:
    return TfidfVectorizer(
        preprocessor=negation_preprocessor,
        stop_words=STOP_WORDS,
        ngram_range=tuple(params["ngram_range"]),
        min_df=params["min_df"],
        sublinear_tf=params.get("sublinear_tf", False),
    )


def build_classifier(kind: str, params: dict, seed: int):
    if kind == "logreg":
        return LogisticRegression(C=params["C"], random_state=seed, **lr.FIXED_CLASSIFIER_PARAMS)
    if kind == "linearsvc":
        return LinearSVC(C=params["C"], class_weight=params["class_weight"], random_state=seed,
                         **svc.FIXED_CLASSIFIER_PARAMS)
    raise StanceModelError(f"Unknown classifier kind {kind!r}; expected one of {CLASSIFIERS}")


class NegationAwareStanceModel:
    def __init__(self, kind: str, vectorizer: TfidfVectorizer, classifier, params: dict):
        if kind not in CLASSIFIERS:
            raise StanceModelError(f"Unknown classifier kind {kind!r}")
        if list(classifier.classes_) != list(range(len(LABELS))):
            raise StanceModelError(
                f"Classifier classes_ {list(classifier.classes_)} do not match the fixed "
                f"four-label index mapping {list(range(len(LABELS)))}"
            )
        self.kind = kind
        self.vectorizer = vectorizer
        self.classifier = classifier
        self.params = params

    @property
    def score_type(self) -> str:
        return "probability" if self.kind == "logreg" else "decision_margin_not_probability"

    @classmethod
    def fit(cls, kind: str, texts: list[str], labels: list[str], params: dict, seed: int = SEED):
        unknown = sorted(set(labels) - set(LABELS))
        if unknown:
            raise StanceModelError(f"Unknown training label(s): {unknown}")
        missing = [label for label in LABELS if label not in set(labels)]
        if missing:
            raise StanceModelError(f"Training data is missing class(es) {missing}; all four are required")
        vectorizer = build_vectorizer(params)
        X = vectorizer.fit_transform([lr.preprocess(t) for t in texts])
        classifier = build_classifier(kind, params, seed)
        classifier.fit(X, np.array([LABEL_TO_INDEX[label] for label in labels]))
        return cls(kind, vectorizer, classifier, params)

    def _transform(self, texts: list[str]):
        if not isinstance(texts, (list, tuple)):
            raise ValueError("texts must be a list of strings")
        return self.vectorizer.transform([lr.preprocess(t) for t in texts])

    def predict_indices(self, texts: list[str]) -> np.ndarray:
        if len(texts) == 0:
            return np.array([], dtype=int)
        return self.classifier.predict(self._transform(texts))

    def predict(self, texts: list[str]) -> list[str]:
        return [LABELS[i] for i in self.predict_indices(texts)]

    def scores(self, texts: list[str]) -> list[dict[str, float]]:
        """Probabilities for logreg; uncalibrated margins for linearsvc (see score_type)."""
        if len(texts) == 0:
            return []
        X = self._transform(texts)
        raw = self.classifier.predict_proba(X) if self.kind == "logreg" else self.classifier.decision_function(X)
        return [{LABELS[j]: float(row[j]) for j in range(len(LABELS))} for row in raw]

    def tokens(self, text: str) -> list[str]:
        return self.vectorizer.build_analyzer()(lr.preprocess(text))

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
        _write_json(artifact_dir / CONFIG_FILE, {**config, "classifier_kind": self.kind})
        hashes = {
            name: ann_schema.sha256_file(artifact_dir / name)
            for name in (VECTORIZER_FILE, MODEL_FILE, LABEL_MAPPING_FILE, CONFIG_FILE)
        }
        _write_json(artifact_dir / METADATA_FILE, {**metadata, "artifact_sha256": hashes})
        return hashes

    @classmethod
    def load(cls, artifact_dir: Path) -> "NegationAwareStanceModel":
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
        return cls(config["classifier_kind"], joblib.load(artifact_dir / VECTORIZER_FILE),
                   joblib.load(artifact_dir / MODEL_FILE), config["selected_hyperparameters"])

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


def _jsonable(params: dict) -> dict:
    return {**params, "ngram_range": list(params["ngram_range"])}


def select_hyperparameters(kind: str, train, val, grid: dict, seed: int = SEED):
    """Uses train and val only. Returns (best_params, all_results)."""
    results, best = [], None
    for params in lr.iter_param_grid(grid):
        model = NegationAwareStanceModel.fit(kind, train.texts, train.labels, params, seed=seed)
        pred = model.predict_indices(val.texts)
        macro = f1_score(val.y, pred, labels=list(range(len(LABELS))), average="macro", zero_division=0)
        results.append({
            "params": _jsonable(params),
            "val_macro_f1": round(float(macro), 4),
            "val_accuracy": round(float(accuracy_score(val.y, pred)), 4),
            "n_features": len(model.vectorizer.vocabulary_),
        })
        if best is None or macro > best[0]:
            best = (macro, params)
    return best[1], results


def support_oppose_confusion(metrics: dict) -> int:
    cm = metrics["confusion_matrix"]["rows_true_cols_pred"]
    s, o = LABEL_TO_INDEX["Support"], LABEL_TO_INDEX["Oppose"]
    return int(cm[s][o] + cm[o][s])


def _summary(train_m: dict, val_m: dict) -> dict:
    return {
        "train_accuracy": train_m["accuracy"],
        "train_macro_f1": train_m["macro_f1"],
        "val_accuracy": val_m["accuracy"],
        "val_macro_f1": val_m["macro_f1"],
        "overfit_gap_macro_f1": round(train_m["macro_f1"] - val_m["macro_f1"], 4),
        "val_recall": {label: val_m["per_class"][label]["recall"] for label in LABELS},
        "val_f1": {label: val_m["per_class"][label]["f1"] for label in LABELS},
        "val_support_oppose_confusions": support_oppose_confusion(val_m),
        "val_confusion_matrix": val_m["confusion_matrix"]["rows_true_cols_pred"],
    }


def previous_summaries(report_paths: dict = PREVIOUS_REPORTS) -> dict:
    """Train/val sections of Experiments 1-2 only; their test metrics are not read."""
    out = {}
    for name, path in report_paths.items():
        path = Path(path)
        if not path.exists():
            out[name] = {"status": "report_not_found", "path": str(path)}
            continue
        report = json.loads(path.read_text(encoding="utf-8"))
        out[name] = {"selected_hyperparameters": report.get("selected_hyperparameters"),
                     **_summary(report["train_metrics"], report["val_metrics"])}
    return out


def _misclassified(val, model, pred) -> list[dict]:
    scores = model.scores(val.texts)
    return [
        {
            "comment_id": val.comment_ids[i],
            "comment_text": val.raw_rows[i]["comment_text"],
            "true_label": LABELS[t],
            "predicted_label": LABELS[p],
            model.score_type: {k: round(v, 4) for k, v in scores[i].items()},
            "annotation_confidence": val.raw_rows[i].get("annotation_confidence", ""),
        }
        for i, (t, p) in enumerate(zip(val.y, pred))
        if t != p
    ]


def run(
    splits_dir: Path = DEFAULT_SPLITS_DIR,
    artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
    previous_reports: dict = PREVIOUS_REPORTS,
    seed: int = SEED,
    grids: dict = PARAM_GRIDS,
    matched_configs: dict = MATCHED_CONFIGS,
) -> dict:
    splits_dir, artifact_dir = Path(splits_dir), Path(artifact_dir)
    if artifact_dir.exists() and any(artifact_dir.iterdir()):
        raise StanceModelError(f"{artifact_dir} is not empty. Refusing to overwrite; use a new model version.")
    manifest_path = splits_dir / "split_manifest.json"
    if not manifest_path.exists():
        raise StanceModelError(f"No split manifest at {manifest_path}; run dataset_prep.py first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    train = load_split(splits_dir / "train.csv")
    val = load_split(splits_dir / "val.csv")

    common_metadata = {
        "generated_utc": ann_schema.utcnow_iso(),
        "split_manifest_source_sha256": manifest.get("source_sha256"),
        "split_manifest_sha256": ann_schema.sha256_file(manifest_path),
        "train_sha256": ann_schema.sha256_file(splits_dir / "train.csv"),
        "val_sha256": ann_schema.sha256_file(splits_dir / "val.csv"),
        "n_train": len(train.labels),
        "n_val": len(val.labels),
        "test_set_status": "development-exposed by Experiment 1; not loaded or scored by this experiment",
        "test_evaluations_performed": 0,
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

    results = {}
    for kind in CLASSIFIERS:
        best_params, tuning = select_hyperparameters(kind, train, val, grids[kind], seed=seed)
        model = NegationAwareStanceModel.fit(kind, train.texts, train.labels, best_params, seed=seed)
        train_m = compute_metrics(train.y, model.predict_indices(train.texts))
        val_pred = model.predict_indices(val.texts)
        val_m = compute_metrics(val.y, val_pred)

        matched = NegationAwareStanceModel.fit(kind, train.texts, train.labels, matched_configs[kind], seed=seed)
        matched_train = compute_metrics(train.y, matched.predict_indices(train.texts))
        matched_val = compute_metrics(val.y, matched.predict_indices(val.texts))

        config = {
            "experiment": EXPERIMENT_NAME,
            "model_version": MODEL_VERSION,
            "seed": seed,
            "labels": list(LABELS),
            "text_field": "normalized_text",
            "preprocessing": "dataset_prep.normalize_text, then negation_preprocessor "
                             "(lowercase, strip accents, unify apostrophes, expand n't), "
                             "then default token_pattern with STOP_WORDS",
            "preserved_terms": sorted(PRESERVED_TERMS),
            "stop_words_count": len(STOP_WORDS),
            "selected_hyperparameters": _jsonable(best_params),
            "param_grid": {k: [list(v) if isinstance(v, tuple) else v for v in vals] for k, vals in grids[kind].items()},
            "selection_criterion": "validation macro-F1 (ties -> first in simplest-first grid order)",
            "vectorizer_fit_on": "train only",
            "classifier_fit_on": "train only",
            "score_type": model.score_type,
        }
        hashes = model.save(artifact_dir / kind, config,
                            {**common_metadata, "n_features": len(model.vectorizer.vocabulary_)})
        results[kind] = {
            "selected_hyperparameters": _jsonable(best_params),
            "tuning_results": tuning,
            "train_metrics": train_m,
            "val_metrics": val_m,
            "summary": _summary(train_m, val_m),
            "matched_config": {"params": _jsonable(matched_configs[kind]),
                               **_summary(matched_train, matched_val)},
            "val_misclassified": _misclassified(val, model, val_pred),
            "top_terms_per_class": model.top_terms(),
            "artifact_sha256": hashes,
        }

    report = {
        "experiment": EXPERIMENT_NAME,
        "model_version": MODEL_VERSION,
        "preserved_terms": sorted(PRESERVED_TERMS),
        "results": results,
        "previous_experiments_train_val_only": previous_summaries(previous_reports),
        "test_set_status": common_metadata["test_set_status"],
    }
    _write_json(artifact_dir / EVAL_REPORT_FILE, report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Experiment 3: negation-aware TF-IDF stance baselines.")
    parser.add_argument("--splits-dir", type=Path, default=DEFAULT_SPLITS_DIR)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args(argv)

    try:
        report = run(args.splits_dir, args.artifact_dir, seed=args.seed)
    except StanceModelError as e:
        print(f"Experiment 3 refused:\n{e}")
        return 1

    for kind, res in report["results"].items():
        print(f"=== {kind} === selected {res['selected_hyperparameters']}")
        print(lr._format_metrics("TRAIN", res["train_metrics"]))
        print(lr._format_metrics("VAL", res["val_metrics"]))
        for label, row in zip(LABELS, res["val_metrics"]["confusion_matrix"]["rows_true_cols_pred"]):
            print(f"  {label:<8} {row}")
        m = res["matched_config"]
        print(f"  matched-config ({m['params']}): val_macro_f1={m['val_macro_f1']} val_acc={m['val_accuracy']}")
    print("Test split: not loaded or scored (development-exposed).")
    print(f"Artifacts: {args.artifact_dir}")
    return 0


if __name__ == "__main__":
    # Re-import by package path so negation_preprocessor pickles as
    # ml.stance_classification.negation_tfidf, not __main__ (unloadable elsewhere).
    from ml.stance_classification import negation_tfidf as _module

    sys.exit(_module.main())

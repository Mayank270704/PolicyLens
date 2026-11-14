import json

import numpy as np
import pytest

from ml.stance_classification import dataset_prep as dp
from ml.stance_classification import tfidf_linearsvc as svc
from ml.stance_classification import tfidf_logreg as lr
from scripts.annotation import schema
from tests.unit.test_tfidf_logreg import _training_texts, _write_split, _write_splits_dir
from tests.unit.test_validate import make_row

PARAMS = {"C": 1.0, "ngram_range": (1, 1), "min_df": 1, "class_weight": "balanced"}
SMALL_GRID = {"C": [0.1, 1.0], "ngram_range": [(1, 1)], "min_df": [1], "class_weight": ["balanced", None]}
PROBES = {
    "Support": "we strongly support and endorse this",
    "Oppose": "we reject and oppose this",
    "Neutral": "a question about the deadline details",
    "Unclear": "perhaps maybe, unsure",
}


@pytest.fixture
def model():
    texts, labels = _training_texts()
    return svc.TfidfLinearSVCStanceModel.fit(texts, labels, PARAMS)


def _fake_logreg_report(path):
    metrics = lr.compute_metrics(np.array([0, 1, 2, 3]), np.array([0, 1, 2, 2]))
    path.write_text(json.dumps({
        "selected_hyperparameters": {"C": 3.0},
        "train_metrics": metrics,
        "val_metrics": metrics,
    }), encoding="utf-8")
    return path


# ---- four-label mapping -----------------------------------------------------

def test_label_mapping_matches_experiment_1():
    assert svc.LABELS == ("Support", "Oppose", "Neutral", "Unclear")
    assert svc.LABEL_TO_INDEX == lr.LABEL_TO_INDEX


def test_predicts_each_of_the_four_classes(model):
    assert model.predict(list(PROBES.values())) == list(PROBES.keys())


def test_classes_align_with_index_mapping(model):
    assert list(model.classifier.classes_) == [0, 1, 2, 3]


def test_misaligned_classes_rejected(model):
    model.classifier.classes_ = np.array([1, 0, 2, 3])
    with pytest.raises(svc.StanceModelError, match="do not match"):
        svc.TfidfLinearSVCStanceModel(model.vectorizer, model.classifier, PARAMS)


def test_decision_scores_cover_all_labels_and_argmax_matches_prediction(model):
    texts = list(PROBES.values())
    for scores, pred in zip(model.decision_scores(texts), model.predict(texts)):
        assert list(scores) == list(svc.LABELS)
        assert max(scores, key=scores.get) == pred


def test_fit_refuses_missing_class():
    texts, labels = _training_texts()
    keep = [i for i, lbl in enumerate(labels) if lbl != "Unclear"]
    with pytest.raises(svc.StanceModelError, match="missing class"):
        svc.TfidfLinearSVCStanceModel.fit([texts[i] for i in keep], [labels[i] for i in keep], PARAMS)


def test_fit_refuses_unknown_label():
    texts, labels = _training_texts()
    with pytest.raises(svc.StanceModelError, match="Unknown training label"):
        svc.TfidfLinearSVCStanceModel.fit(texts + ["x"], labels + ["Mixed"], PARAMS)


# ---- serialization ---------------------------------------------------------

def test_save_and_reload_identical(model, tmp_path):
    texts = list(PROBES.values())
    model.save(tmp_path / "art", {"selected_hyperparameters": {**PARAMS, "ngram_range": [1, 1]}}, {})
    reloaded = svc.TfidfLinearSVCStanceModel.load(tmp_path / "art")
    assert reloaded.predict(texts) == model.predict(texts)
    for a, b in zip(reloaded.decision_scores(texts), model.decision_scores(texts)):
        assert a == pytest.approx(b)
    mapping = json.loads((tmp_path / "art" / svc.LABEL_MAPPING_FILE).read_text(encoding="utf-8"))
    assert mapping["labels"] == list(svc.LABELS)


def test_load_refuses_tampered_artifact(model, tmp_path):
    model.save(tmp_path / "art", {"selected_hyperparameters": PARAMS}, {})
    with open(tmp_path / "art" / svc.VECTORIZER_FILE, "ab") as f:
        f.write(b"x")
    with pytest.raises(svc.StanceModelError, match="SHA-256 mismatch"):
        svc.TfidfLinearSVCStanceModel.load(tmp_path / "art")


def test_load_refuses_missing_metadata(tmp_path):
    with pytest.raises(svc.StanceModelError, match="No training_metadata.json"):
        svc.TfidfLinearSVCStanceModel.load(tmp_path)


# ---- preprocessing ---------------------------------------------------------

def test_preprocessing_is_shared_with_experiment_1():
    assert svc.preprocess is lr.preprocess
    assert svc.load_split is lr.load_split
    assert svc.FIXED_VECTORIZER_PARAMS["stop_words"] == lr.FIXED_VECTORIZER_PARAMS["stop_words"]


def test_whitespace_variants_score_identically(model):
    a = model.decision_scores(["we strongly support this"])[0]
    b = model.decision_scores(["  we\tstrongly \n support   this "])[0]
    assert a == pytest.approx(b)
    assert svc.preprocess("  a \n b ") == dp.normalize_text("  a \n b ")


# ---- invalid input ---------------------------------------------------------

@pytest.mark.parametrize("bad", [None, "", "  \t\n", 42, {"text": "x"}])
def test_invalid_inputs_raise(model, bad):
    with pytest.raises(ValueError):
        model.predict([bad])
    with pytest.raises(ValueError):
        model.decision_scores([bad])


def test_non_list_input_raises(model):
    with pytest.raises(ValueError, match="list of strings"):
        model.predict("a string, not a list")


def test_empty_batch(model):
    assert model.predict([]) == []
    assert model.decision_scores([]) == []


# ---- end-to-end: test split never scored, no overwrite ---------------------

def test_run_never_scores_test_split(tmp_path):
    splits_dir = _write_splits_dir(tmp_path)
    # A test.csv that load_split would reject: proves run() never loads it for prediction.
    row = make_row(comment_id="PL-999999", comment_text="x", annotator_label="Mixed", annotation_confidence="3")
    row["normalized_text"] = "x"
    schema.write_rows_atomic(splits_dir / "test.csv", [row], dp.SPLIT_COLUMNS)

    art = tmp_path / "art"
    report = svc.run(splits_dir, art, _fake_logreg_report(tmp_path / "lr.json"), grid=SMALL_GRID)

    assert "test_metrics" not in report
    assert len(report["tuning_results"]) == 4
    assert set(report["val_metrics"]["per_class"]) == set(svc.LABELS)
    metadata = json.loads((art / svc.METADATA_FILE).read_text(encoding="utf-8"))
    assert metadata["test_evaluations_performed"] == 0
    for name in (svc.VECTORIZER_FILE, svc.MODEL_FILE, svc.LABEL_MAPPING_FILE, svc.CONFIG_FILE,
                 svc.METADATA_FILE, svc.EVAL_REPORT_FILE):
        assert (art / name).exists()


def test_run_refuses_to_overwrite(tmp_path):
    splits_dir = _write_splits_dir(tmp_path)
    art = tmp_path / "art"
    lr_report = _fake_logreg_report(tmp_path / "lr.json")
    svc.run(splits_dir, art, lr_report, grid=SMALL_GRID)
    with pytest.raises(svc.StanceModelError, match="Refusing to overwrite"):
        svc.run(splits_dir, art, lr_report, grid=SMALL_GRID)


def test_vocabulary_from_train_only(tmp_path):
    splits_dir = _write_splits_dir(tmp_path)
    svc.run(splits_dir, tmp_path / "art", _fake_logreg_report(tmp_path / "lr.json"), grid=SMALL_GRID)
    vocab = set(svc.TfidfLinearSVCStanceModel.load(tmp_path / "art").vectorizer.vocabulary_)
    assert "indeed" not in vocab  # val-only token


def test_comparison_uses_only_train_and_val(tmp_path):
    lr_report = _fake_logreg_report(tmp_path / "lr.json")  # contains no test_metrics at all
    m = lr.compute_metrics(np.array([0, 1, 2, 3]), np.array([0, 1, 2, 3]))
    cmp = svc.compare_with_logreg(m, m, lr_report)
    assert cmp["status"] == "ok"
    assert cmp["linearsvc"]["overfit_gap_macro_f1"] == 0.0
    assert set(cmp["logreg"]["val_per_class"]) == set(svc.LABELS)


def test_comparison_handles_missing_logreg_report(tmp_path):
    m = lr.compute_metrics(np.array([0, 1]), np.array([0, 1]))
    assert svc.compare_with_logreg(m, m, tmp_path / "missing.json")["status"] == "logreg_report_not_found"


def test_selection_is_deterministic():
    texts, labels = _training_texts()
    train = lr.SplitData([str(i) for i in range(len(texts))], texts, labels, [])
    val = lr.SplitData(["a", "b", "c", "d"], list(PROBES.values()), list(PROBES.keys()), [])
    assert svc.select_hyperparameters(train, val, grid=SMALL_GRID) == svc.select_hyperparameters(train, val, grid=SMALL_GRID)

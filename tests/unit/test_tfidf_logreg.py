import json

import numpy as np
import pytest

from ml.stance_classification import dataset_prep as dp
from ml.stance_classification import tfidf_logreg as tl
from scripts.annotation import schema
from tests.unit.test_validate import make_row

CLASS_VOCAB = {
    "Support": ["strongly support this proposal", "great policy fully endorse", "support endorse welcome"],
    "Oppose": ["reject this proposal entirely", "oppose harmful policy reject", "against reject oppose"],
    "Neutral": ["question about timeline details", "what is the deadline question", "information request details"],
    "Unclear": ["maybe perhaps not sure", "unsure perhaps hard say", "perhaps maybe unsure"],
}
PARAMS = {"C": 10.0, "ngram_range": (1, 1), "min_df": 1, "sublinear_tf": True}
SMALL_GRID = {"C": [1.0, 10.0], "ngram_range": [(1, 1)], "min_df": [1], "sublinear_tf": [True]}


def _training_texts():
    texts, labels = [], []
    for label, examples in CLASS_VOCAB.items():
        for ex in examples:
            texts.append(ex)
            labels.append(label)
    return texts, labels


@pytest.fixture
def model():
    texts, labels = _training_texts()
    return tl.TfidfLogRegStanceModel.fit(texts, labels, PARAMS)


def _write_split(path, label_texts, start=0):
    rows = []
    for i, (label, text) in enumerate(label_texts):
        row = make_row(comment_id=f"PL-{start + i:06d}", comment_text=text, annotator_label=label,
                       annotation_confidence="3", annotation_notes="note" if label == "Unclear" else "")
        row["normalized_text"] = dp.normalize_text(text)
        rows.append(row)
    schema.write_rows_atomic(path, rows, dp.SPLIT_COLUMNS)


def _write_splits_dir(tmp_path):
    texts, labels = _training_texts()
    splits_dir = tmp_path / "splits"
    splits_dir.mkdir()
    _write_split(splits_dir / "train.csv", list(zip(labels, texts)), start=0)
    _write_split(splits_dir / "val.csv", [(lbl, exs[0] + " indeed") for lbl, exs in CLASS_VOCAB.items()], start=100)
    _write_split(splits_dir / "test.csv", [(lbl, exs[1] + " today") for lbl, exs in CLASS_VOCAB.items()], start=200)
    (splits_dir / "split_manifest.json").write_text(json.dumps({"source_sha256": "fixture"}), encoding="utf-8")
    return splits_dir


# ---- four-class predictions -------------------------------------------------

def test_label_mapping_is_fixed_four_classes():
    assert tl.LABELS == ("Support", "Oppose", "Neutral", "Unclear")
    assert tl.LABEL_TO_INDEX == {"Support": 0, "Oppose": 1, "Neutral": 2, "Unclear": 3}


def test_predicts_each_of_the_four_classes(model):
    probes = {
        "Support": "we strongly support and endorse this",
        "Oppose": "we reject and oppose this",
        "Neutral": "a question about the deadline details",
        "Unclear": "perhaps maybe, unsure",
    }
    preds = model.predict(list(probes.values()))
    assert preds == list(probes.keys())
    assert set(preds) == set(tl.LABELS)


def test_fit_refuses_when_a_class_is_missing():
    texts, labels = _training_texts()
    keep = [i for i, lbl in enumerate(labels) if lbl != "Oppose"]
    with pytest.raises(tl.StanceModelError, match="missing class"):
        tl.TfidfLogRegStanceModel.fit([texts[i] for i in keep], [labels[i] for i in keep], PARAMS)


def test_fit_refuses_unknown_label():
    texts, labels = _training_texts()
    with pytest.raises(tl.StanceModelError, match="Unknown training label"):
        tl.TfidfLogRegStanceModel.fit(texts + ["x y z"], labels + ["Mixed"], PARAMS)


# ---- probability / class mapping -------------------------------------------

def test_probabilities_cover_all_labels_and_match_prediction(model):
    texts = ["strongly support", "reject oppose", "deadline question", "perhaps unsure"]
    probas = model.predict_proba(texts)
    preds = model.predict(texts)
    for proba, pred in zip(probas, preds):
        assert list(proba) == list(tl.LABELS)
        assert sum(proba.values()) == pytest.approx(1.0)
        assert max(proba, key=proba.get) == pred


def test_classifier_classes_align_with_index_mapping(model):
    assert list(model.classifier.classes_) == [0, 1, 2, 3]


def test_misaligned_classifier_classes_are_rejected(model):
    model.classifier.classes_ = np.array([3, 2, 1, 0])
    with pytest.raises(tl.StanceModelError, match="do not match"):
        tl.TfidfLogRegStanceModel(model.vectorizer, model.classifier, PARAMS)


# ---- serialization ---------------------------------------------------------

def test_save_and_reload_gives_identical_predictions(model, tmp_path):
    texts = ["strongly support", "reject oppose", "deadline question", "perhaps unsure"]
    config = {"selected_hyperparameters": {**PARAMS, "ngram_range": [1, 1]}}
    model.save(tmp_path / "art", config, {"note": "fixture"})

    reloaded = tl.TfidfLogRegStanceModel.load(tmp_path / "art")
    assert reloaded.predict(texts) == model.predict(texts)
    for a, b in zip(reloaded.predict_proba(texts), model.predict_proba(texts)):
        assert a == pytest.approx(b)
    mapping = json.loads((tmp_path / "art" / tl.LABEL_MAPPING_FILE).read_text(encoding="utf-8"))
    assert mapping["labels"] == list(tl.LABELS)


def test_load_refuses_tampered_artifact(model, tmp_path):
    model.save(tmp_path / "art", {"selected_hyperparameters": PARAMS}, {})
    with open(tmp_path / "art" / tl.MODEL_FILE, "ab") as f:
        f.write(b"tamper")
    with pytest.raises(tl.StanceModelError, match="SHA-256 mismatch"):
        tl.TfidfLogRegStanceModel.load(tmp_path / "art")


def test_load_refuses_missing_metadata(tmp_path):
    with pytest.raises(tl.StanceModelError, match="No training_metadata.json"):
        tl.TfidfLogRegStanceModel.load(tmp_path)


# ---- preprocessing consistency ---------------------------------------------

def test_preprocess_matches_dataset_prep_normalization():
    raw = "  Strongly\n\tsupport   this  "
    assert tl.preprocess(raw) == dp.normalize_text(raw) == "Strongly support this"


def test_whitespace_variants_predict_identically(model):
    a = model.predict_proba(["we strongly support this"])
    b = model.predict_proba(["  we\tstrongly \n support   this "])
    assert a[0] == pytest.approx(b[0])


def test_load_split_rejects_preprocessing_drift(tmp_path):
    path = tmp_path / "train.csv"
    row = make_row(comment_id="PL-000001", comment_text="a  b", annotator_label="Support",
                   annotation_confidence="3")
    row["normalized_text"] = "a  b"  # not normalized
    schema.write_rows_atomic(path, [row], dp.SPLIT_COLUMNS)
    with pytest.raises(tl.StanceModelError, match="preprocessing drift"):
        tl.load_split(path)


def test_load_split_rejects_invalid_label(tmp_path):
    path = tmp_path / "train.csv"
    _write_split(path, [("Mixed", "some text")])
    with pytest.raises(tl.StanceModelError, match="invalid label"):
        tl.load_split(path)


# ---- invalid input ---------------------------------------------------------

@pytest.mark.parametrize("bad", [None, "", "   \n\t", 123, ["list"]])
def test_invalid_single_inputs_raise(model, bad):
    with pytest.raises(ValueError):
        model.predict([bad])


def test_non_list_input_raises(model):
    with pytest.raises(ValueError, match="list of strings"):
        model.predict("not a list")


def test_empty_batch_returns_empty(model):
    assert model.predict([]) == []
    assert model.predict_proba([]) == []


def test_load_split_missing_file(tmp_path):
    with pytest.raises(tl.StanceModelError, match="not found"):
        tl.load_split(tmp_path / "nope.csv")


# ---- end-to-end run on fixture splits ---------------------------------------

def test_run_end_to_end_and_refuses_rescoring(tmp_path):
    splits_dir = _write_splits_dir(tmp_path)
    art = tmp_path / "art"
    report = tl.run(splits_dir, art, grid=SMALL_GRID)

    assert report["test_metrics"]["n"] == 4
    assert set(report["test_metrics"]["per_class"]) == set(tl.LABELS)
    assert len(report["tuning_results"]) == 2
    for name in (tl.VECTORIZER_FILE, tl.MODEL_FILE, tl.LABEL_MAPPING_FILE, tl.CONFIG_FILE,
                 tl.METADATA_FILE, tl.EVAL_REPORT_FILE):
        assert (art / name).exists()
    metadata = json.loads((art / tl.METADATA_FILE).read_text(encoding="utf-8"))
    assert metadata["test_evaluations_performed"] == 1

    with pytest.raises(tl.StanceModelError, match="Refusing to retrain"):
        tl.run(splits_dir, art, grid=SMALL_GRID)


def test_vectorizer_vocabulary_comes_from_train_only(tmp_path):
    splits_dir = _write_splits_dir(tmp_path)
    tl.run(splits_dir, tmp_path / "art", grid=SMALL_GRID)
    model = tl.TfidfLogRegStanceModel.load(tmp_path / "art")
    vocab = set(model.vectorizer.vocabulary_)
    # "indeed" exists only in val, "today" only in test
    assert "indeed" not in vocab
    assert "today" not in vocab


def test_select_hyperparameters_is_deterministic():
    texts, labels = _training_texts()
    train = tl.SplitData(comment_ids=[str(i) for i in range(len(texts))], texts=texts, labels=labels, raw_rows=[])
    val = tl.SplitData(comment_ids=["a", "b", "c", "d"],
                       texts=["support endorse", "reject oppose", "deadline question", "perhaps unsure"],
                       labels=list(tl.LABELS), raw_rows=[])
    first = tl.select_hyperparameters(train, val, grid=SMALL_GRID)
    second = tl.select_hyperparameters(train, val, grid=SMALL_GRID)
    assert first == second

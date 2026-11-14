import json

import numpy as np
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer

from ml.stance_classification import dataset_prep as dp
from ml.stance_classification import negation_tfidf as nt
from ml.stance_classification import tfidf_logreg as lr
from scripts.annotation import schema
from tests.unit.test_tfidf_logreg import _training_texts, _write_splits_dir
from tests.unit.test_validate import make_row

LR_PARAMS = {"C": 10.0, "ngram_range": (1, 2), "min_df": 1, "sublinear_tf": False}
SVC_PARAMS = {"C": 1.0, "ngram_range": (1, 2), "min_df": 1, "class_weight": "balanced"}
PARAMS = {"logreg": LR_PARAMS, "linearsvc": SVC_PARAMS}
SMALL_GRIDS = {
    "logreg": {"C": [1.0, 10.0], "ngram_range": [(1, 2)], "min_df": [1], "sublinear_tf": [False]},
    "linearsvc": {"C": [0.3, 1.0], "ngram_range": [(1, 2)], "min_df": [1], "class_weight": ["balanced"]},
}

# Support and Oppose differ only by negation, so a model can only separate
# them if negation survives preprocessing.
MINIMAL_PAIRS = [
    ("Support", "I support this plan"), ("Oppose", "I do not support this plan"),
    ("Support", "we support the proposal"), ("Oppose", "we don't support the proposal"),
    ("Support", "they agree with the change"), ("Oppose", "they never agree with the change"),
    ("Support", "good policy support it"), ("Oppose", "no support for this policy"),
    ("Neutral", "question about the timeline"), ("Neutral", "what is the deadline"),
    ("Neutral", "request for details"), ("Unclear", "maybe perhaps unsure"),
    ("Unclear", "hard to say perhaps"), ("Unclear", "unsure maybe"),
]


def _pairs_model(kind):
    labels, texts = zip(*MINIMAL_PAIRS)
    return nt.NegationAwareStanceModel.fit(kind, list(texts), list(labels), PARAMS[kind])


# ---- preprocessing ---------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("I CAN'T accept", "i cannot accept"),
    ("We can’t accept", "we cannot accept"),
    ("won't work", "will not work"),
    ("I don’t support it", "i do not support it"),
    ("It isn`t working", "it is not working"),
    ("shan't", "shall not"),
    ("Café résumé", "cafe resume"),
    ("I cannot agree", "i cannot agree"),
])
def test_negation_preprocessor(raw, expected):
    assert nt.negation_preprocessor(raw) == expected


@pytest.mark.parametrize("term", sorted(nt.PRESERVED_TERMS))
def test_every_preserved_term_survives_tokenization(term):
    analyzer = nt.build_vectorizer({"ngram_range": (1, 1), "min_df": 1}).build_analyzer()
    assert analyzer(term) == [term]
    assert term not in nt.STOP_WORDS


def test_required_terms_are_preserved():
    required = {"not", "no", "nor", "never", "against", "without", "but", "however",
                "although", "cannot", "none", "nothing"}
    assert required <= nt.PRESERVED_TERMS


def test_uninformative_words_still_removed():
    analyzer = nt.build_vectorizer({"ngram_range": (1, 1), "min_df": 1}).build_analyzer()
    assert analyzer("the and of is it this") == []


def test_negated_phrase_keeps_negation_bigram():
    analyzer = nt.build_vectorizer({"ngram_range": (1, 2), "min_df": 1}).build_analyzer()
    assert "not favour" in analyzer("I am not in favour")
    assert "not support" in analyzer("I don't support this")
    assert analyzer("No, never, against it") == ["no", "never", "against", "no never", "never against"]


def test_old_config_conflates_positive_and_negative_but_new_does_not():
    texts = ["I support this", "I do not support this", "I can't support this"]
    old = TfidfVectorizer(ngram_range=(1, 2), **lr.FIXED_VECTORIZER_PARAMS).fit(texts).transform(texts).toarray()
    new = nt.build_vectorizer({"ngram_range": (1, 2), "min_df": 1}).fit(texts).transform(texts).toarray()
    assert np.allclose(old[0], old[1]) and np.allclose(old[0], old[2])
    assert not np.allclose(new[0], new[1])
    assert not np.allclose(new[0], new[2])


def test_whitespace_and_apostrophe_variants_identical():
    model = _pairs_model("logreg")
    a = model.scores(["we don't support this"])[0]
    b = model.scores(["  we   don’t\nsupport this "])[0]
    assert a == pytest.approx(b)


# ---- positive vs negative wording, both classifiers -------------------------

@pytest.mark.parametrize("kind", nt.CLASSIFIERS)
def test_positive_vs_negated_wording_predicted_differently(kind):
    model = _pairs_model(kind)
    assert model.predict(["you support the plan"]) == ["Support"]
    assert model.predict(["you do not support the plan"]) == ["Oppose"]
    assert model.predict(["you don’t support the plan"]) == ["Oppose"]


@pytest.mark.parametrize("kind", nt.CLASSIFIERS)
def test_all_four_classes_predicted(kind):
    model = _pairs_model(kind)
    preds = model.predict(["we support it", "we do not support it", "a deadline question", "perhaps unsure"])
    assert preds == ["Support", "Oppose", "Neutral", "Unclear"]


@pytest.mark.parametrize("kind", nt.CLASSIFIERS)
def test_scores_cover_labels_and_argmax_matches(kind):
    model = _pairs_model(kind)
    texts = ["we support it", "we do not support it"]
    for s, p in zip(model.scores(texts), model.predict(texts)):
        assert list(s) == list(nt.LABELS)
        assert max(s, key=s.get) == p
    if kind == "logreg":
        assert sum(model.scores(texts)[0].values()) == pytest.approx(1.0)
        assert model.score_type == "probability"
    else:
        assert model.score_type == "decision_margin_not_probability"


def test_label_mapping_and_alignment():
    assert nt.LABELS == ("Support", "Oppose", "Neutral", "Unclear")
    model = _pairs_model("logreg")
    model.classifier.classes_ = np.array([3, 2, 1, 0])
    with pytest.raises(nt.StanceModelError, match="do not match"):
        nt.NegationAwareStanceModel("logreg", model.vectorizer, model.classifier, LR_PARAMS)


def test_fit_refuses_missing_class_and_unknown_kind():
    texts, labels = _training_texts()
    keep = [i for i, lbl in enumerate(labels) if lbl != "Oppose"]
    with pytest.raises(nt.StanceModelError, match="missing class"):
        nt.NegationAwareStanceModel.fit("logreg", [texts[i] for i in keep], [labels[i] for i in keep], LR_PARAMS)
    with pytest.raises(nt.StanceModelError, match="Unknown classifier kind"):
        nt.NegationAwareStanceModel.fit("svm_rbf", texts, labels, LR_PARAMS)


# ---- serialization ---------------------------------------------------------

@pytest.mark.parametrize("kind", nt.CLASSIFIERS)
def test_save_reload_identical(kind, tmp_path):
    model = _pairs_model(kind)
    texts = ["we support it", "we don't support it", "deadline question", "perhaps"]
    model.save(tmp_path / kind, {"selected_hyperparameters": nt._jsonable(PARAMS[kind])}, {})
    reloaded = nt.NegationAwareStanceModel.load(tmp_path / kind)
    assert reloaded.kind == kind
    assert reloaded.predict(texts) == model.predict(texts)
    for a, b in zip(reloaded.scores(texts), model.scores(texts)):
        assert a == pytest.approx(b)
    assert reloaded.tokens("I can't agree") == ["cannot", "agree", "cannot agree"]


def test_load_refuses_tampered(tmp_path):
    model = _pairs_model("linearsvc")
    model.save(tmp_path / "a", {"selected_hyperparameters": nt._jsonable(SVC_PARAMS)}, {})
    with open(tmp_path / "a" / nt.MODEL_FILE, "ab") as f:
        f.write(b"x")
    with pytest.raises(nt.StanceModelError, match="SHA-256 mismatch"):
        nt.NegationAwareStanceModel.load(tmp_path / "a")


# ---- invalid input ---------------------------------------------------------

@pytest.mark.parametrize("bad", [None, "", "   ", 7, ["x"]])
def test_invalid_inputs_raise(bad):
    model = _pairs_model("logreg")
    with pytest.raises(ValueError):
        model.predict([bad])
    with pytest.raises(ValueError):
        model.scores([bad])


def test_non_list_and_empty_batch():
    model = _pairs_model("linearsvc")
    with pytest.raises(ValueError, match="list of strings"):
        model.predict("text")
    assert model.predict([]) == []
    assert model.scores([]) == []


# ---- end-to-end ------------------------------------------------------------

def _run(tmp_path, splits_dir, art):
    return nt.run(splits_dir, art, previous_reports={"exp1_logreg": tmp_path / "missing.json"},
                  grids=SMALL_GRIDS, matched_configs=PARAMS)


def test_run_trains_both_never_touches_test(tmp_path):
    splits_dir = _write_splits_dir(tmp_path)
    row = make_row(comment_id="PL-999999", comment_text="x", annotator_label="Mixed", annotation_confidence="3")
    row["normalized_text"] = "x"
    schema.write_rows_atomic(splits_dir / "test.csv", [row], dp.SPLIT_COLUMNS)

    art = tmp_path / "art"
    report = _run(tmp_path, splits_dir, art)
    assert set(report["results"]) == {"logreg", "linearsvc"}
    for kind, res in report["results"].items():
        assert "test_metrics" not in res
        assert len(res["tuning_results"]) == 2
        assert set(res["val_metrics"]["per_class"]) == set(nt.LABELS)
        assert "val_support_oppose_confusions" in res["summary"]
        assert res["matched_config"]["params"]["C"] == PARAMS[kind]["C"]
        metadata = json.loads((art / kind / nt.METADATA_FILE).read_text(encoding="utf-8"))
        assert metadata["test_evaluations_performed"] == 0
        assert "test_sha256" not in metadata
        vocab = set(nt.NegationAwareStanceModel.load(art / kind).vectorizer.vocabulary_)
        assert "indeed" not in vocab  # val-only token
    assert report["previous_experiments_train_val_only"]["exp1_logreg"]["status"] == "report_not_found"
    assert (art / nt.EVAL_REPORT_FILE).exists()


def test_run_refuses_nonempty_artifact_dir(tmp_path):
    splits_dir = _write_splits_dir(tmp_path)
    art = tmp_path / "art"
    _run(tmp_path, splits_dir, art)
    with pytest.raises(nt.StanceModelError, match="Refusing to overwrite"):
        _run(tmp_path, splits_dir, art)


def test_artifacts_from_script_run_load_in_another_process(tmp_path):
    import subprocess
    import sys

    splits_dir = _write_splits_dir(tmp_path)
    art = tmp_path / "art"
    script = schema.REPO_ROOT / "ml" / "stance_classification" / "negation_tfidf.py"
    subprocess.run([sys.executable, str(script), "--splits-dir", str(splits_dir), "--artifact-dir", str(art)],
                   check=True, capture_output=True)
    for kind in nt.CLASSIFIERS:
        model = nt.NegationAwareStanceModel.load(art / kind)
        assert model.vectorizer.preprocessor.__module__ == "ml.stance_classification.negation_tfidf"
        assert len(model.predict(["we do not support it"])) == 1


def test_previous_summaries_read_train_val_only(tmp_path):
    m = lr.compute_metrics(np.array([0, 1, 2, 3]), np.array([0, 0, 2, 3]))
    path = tmp_path / "prev.json"
    path.write_text(json.dumps({"selected_hyperparameters": {}, "train_metrics": m, "val_metrics": m}),
                    encoding="utf-8")
    out = nt.previous_summaries({"prev": path})["prev"]
    assert out["val_support_oppose_confusions"] == 1
    assert out["overfit_gap_macro_f1"] == 0.0

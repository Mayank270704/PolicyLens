"""Indian stance training framework: refusal rules, group-aware splits, leakage checks,
reproducibility and single-use test evaluation. Synthetic data only."""
import json
import re
from pathlib import Path

import pandas as pd
import pytest

from ml.indian_stance import data_loader, evaluate, splits, train
from ml.indian_stance.common import REPO_ROOT

CONFIG = REPO_ROOT / "configs" / "indian_stance" / "baseline_v1.json"
VOCAB = {"Support": "welcome endorse back good open", "Oppose": "withdraw reject scrap harmful against",
         "Neutral": "question clarify when how which", "Unclear": "maybe perhaps depends unsure either"}


def labelled(n_per_class=12, **overrides):
    rows = []
    for lab, words in VOCAB.items():
        w = words.split()
        for i in range(n_per_class):
            # two class cue words + four row-unique tokens: same-class texts stay far below the
            # 0.8 near-duplicate threshold, so the fixture itself is leakage-free
            unique = " ".join(f"{lab[:2].lower()}{i}{s}" for s in "abcd")
            rows.append({"item_id": f"{lab[:3]}{i}", "source": "mygov",
                         "text": f"{w[i % 5]} {w[(i + 2) % 5]} {unique}",
                         "stance": lab, "label_source": "human_adjudicated", "adjudication_status": "adjudicated",
                         "annotator_ids": "annotator_A;annotator_B", "text_group_id": f"g{lab}{i}",
                         "author_group_id": "", "split": ""})
    df = pd.DataFrame(rows)
    for k, v in overrides.items():
        df[k] = v
    return df


def save(df, tmp_path, name="labels.csv"):
    p = tmp_path / name
    df.to_csv(p, index=False)
    return p


def small_config(tmp_path):
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    for m in cfg["models"]:
        m["grid"] = {k: v[:1] for k, v in m["grid"].items()}
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p


# ---- refusal rules -----------------------------------------------------------

def test_refuses_absent_labels(tmp_path):
    with pytest.raises(data_loader.LabelValidationError, match="no stance label"):
        data_loader.load_labelled(save(labelled(stance=""), tmp_path))


def test_refuses_blank_template_columns(tmp_path):
    p = tmp_path / "template.csv"
    pd.DataFrame({"item_id": ["MYG2-0001"], "stance": [""], "annotator_id": [""]}).to_csv(p, index=False)
    with pytest.raises(data_loader.LabelValidationError, match="missing required columns"):
        data_loader.load_labelled(p)


@pytest.mark.parametrize("value", ["positive", "negative", "4", "0"])
def test_refuses_sentiment_labels(tmp_path, value):
    with pytest.raises(data_loader.LabelValidationError, match="sentiment"):
        data_loader.load_labelled(save(labelled(stance=value), tmp_path))


@pytest.mark.parametrize("source", ["weak_model_prediction_NOT_ground_truth:sentiment140_hashing_sgd_v1",
                                    "pseudo_label_sentiment140_heuristic_v1", "ai_working_label", "human"])
def test_refuses_non_human_label_sources(tmp_path, source):
    with pytest.raises(data_loader.LabelValidationError, match="label_source"):
        data_loader.load_labelled(save(labelled(label_source=source), tmp_path))


def test_refuses_unadjudicated_and_single_annotator(tmp_path):
    with pytest.raises(data_loader.LabelValidationError, match="not adjudicated"):
        data_loader.load_labelled(save(labelled(adjudication_status="single_pass"), tmp_path))
    with pytest.raises(data_loader.LabelValidationError, match="two distinct annotator"):
        data_loader.load_labelled(save(labelled(annotator_ids="annotator_A"), tmp_path))


@pytest.mark.parametrize("source", ["civis", "lok_sabha", "sentiment140"])
def test_refuses_context_only_sources(tmp_path, source):
    with pytest.raises(data_loader.LabelValidationError, match="never stance examples"):
        data_loader.load_labelled(save(labelled(source=source), tmp_path))


def test_refuses_unjustified_multi_source_merge(tmp_path):
    df = labelled()
    df.loc[df.index[::2], "source"] = "tweets"
    p = save(df, tmp_path)
    with pytest.raises(data_loader.LabelValidationError, match="merge-justification"):
        data_loader.load_labelled(p)
    assert len(data_loader.load_labelled(p, True, "pilot pooled to test source transfer explicitly")) == len(df)


def test_train_cli_refuses_sentiment_labels(tmp_path):
    p = save(labelled(stance="positive"), tmp_path)
    assert train.main(["--data", str(p), "--config", str(small_config(tmp_path)), "--out-dir", str(tmp_path / "run")]) == 2
    assert not (tmp_path / "run").exists()


def test_refuses_too_few_examples(tmp_path):
    with pytest.raises(train.TrainingRefused, match="too few"):
        train.run(save(labelled(n_per_class=3), tmp_path), small_config(tmp_path), tmp_path / "run")


# ---- group-aware splits and leakage --------------------------------------------

def test_components_join_shared_text_and_author():
    df = pd.DataFrame({"item_id": ["a", "b", "c", "d"], "text_group_id": ["t1", "t1", "t2", "t3"],
                       "author_group_id": ["", "", "u1", "u1"]})
    c = splits.components(df)
    assert c[0] == c[1] and c[2] == c[3] and c[0] != c[2]


def test_assign_splits_never_splits_a_component():
    df = labelled()
    df.loc[df.index[:10], "text_group_id"] = "shared"
    out = splits.assign_splits(df, seed=1)
    assert out.groupby("component").assigned_split.nunique().max() == 1
    assert splits.check_leakage(out, near_dup_threshold=None)["text_group_id_crossing"] == 0


def test_locked_test_is_honoured_and_crossing_component_refused():
    df = labelled()
    df.loc[df.index[:8], "split"] = "locked_test"
    out = splits.assign_splits(df, seed=1)
    assert set(out.item_id[out.assigned_split == "test"]) == set(df.item_id[:8])
    df.loc[df.index[8], "text_group_id"] = df.loc[df.index[0], "text_group_id"]
    with pytest.raises(splits.LeakageError, match="locked test"):
        splits.assign_splits(df, seed=1)


def test_leakage_checker_detects_text_and_near_duplicates():
    df = pd.DataFrame({"item_id": ["a", "b", "c"], "text_group_id": ["1", "2", "3"], "author_group_id": ["", "", ""],
                       "text": ["withdraw the licence now", "Withdraw the licence now", "metro is great"],
                       "assigned_split": ["train", "test", "val"]})
    with pytest.raises(splits.LeakageError, match="normalised_text"):
        splits.check_leakage(df)
    df.loc[1, "text"] = "withdraw the licence now please"
    with pytest.raises(splits.LeakageError, match="near-duplicate"):
        splits.check_leakage(df, near_dup_threshold=0.7)


# ---- training, reproducibility, single-use evaluation ------------------------------

def test_training_is_reproducible_and_test_is_single_use(tmp_path):
    data, cfg = save(labelled(), tmp_path), small_config(tmp_path)
    m1 = train.run(data, cfg, tmp_path / "run1")
    m2 = train.run(data, cfg, tmp_path / "run2")
    assert (tmp_path / "run1" / "splits.csv").read_text() == (tmp_path / "run2" / "splits.csv").read_text()
    assert m1["selected"] == m2["selected"] and m1["test_evaluations_performed"] == 0
    assert json.loads((tmp_path / "run1" / "selection_results.json").read_text()) == \
        json.loads((tmp_path / "run2" / "selection_results.json").read_text())
    res = evaluate.run(tmp_path / "run1", data)
    assert set(res["overall"]["per_class"]) == {"Support", "Oppose", "Neutral", "Unclear"}
    assert "macro_f1" in res["overall"] and "weighted_f1" in res["overall"]
    errors = (tmp_path / "run1" / "test_evaluation" / "error_analysis.csv").read_text(encoding="utf-8")
    assert not re.search(r"\b[a-z]{2}\d+[abcd]\b", errors), "error analysis must not contain text tokens"
    with pytest.raises(evaluate.EvaluationRefused, match="single-use"):
        evaluate.run(tmp_path / "run1", data)


def test_evaluate_refuses_changed_data(tmp_path):
    data, cfg = save(labelled(), tmp_path), small_config(tmp_path)
    train.run(data, cfg, tmp_path / "run")
    df = pd.read_csv(data, dtype=str, keep_default_na=False)
    df.loc[0, "stance"] = "Oppose"
    df.to_csv(data, index=False)
    with pytest.raises(evaluate.EvaluationRefused, match="differs"):
        evaluate.run(tmp_path / "run", data)


def test_token_pattern_keeps_devanagari_words_whole():
    words = re.findall(train.TOKEN_PATTERN, "मुझे यह लाइसेंस पसंद नहीं")
    assert words == ["मुझे", "यह", "लाइसेंस", "पसंद", "नहीं"]
    assert re.findall(train.TOKEN_PATTERN, "do not withdraw") == ["do", "not", "withdraw"]

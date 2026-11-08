import json

import pytest

from ml.stance_classification import dataset_prep as dp
from scripts.annotation import schema
from tests.unit.test_validate import make_row


def _rows(n, label_cycle=("Support", "Oppose", "Neutral", "Unclear")):
    rows = []
    for i in range(n):
        label = label_cycle[i % len(label_cycle)]
        notes = "note" if label == "Unclear" else ""
        rows.append(make_row(
            comment_id=f"PL-{i:04d}", comment_text=f"comment number {i} about the policy",
            annotator_label=label, annotation_confidence="2", annotation_notes=notes,
        ))
    return rows


# ---- loading ---------------------------------------------------------------

def test_load_finalized_annotations_refuses_if_missing(tmp_path):
    with pytest.raises(dp.DatasetPrepError, match="No finalized annotation export"):
        dp.load_finalized_annotations(tmp_path / "does_not_exist.csv")


def test_load_finalized_annotations_reads_real_file(tmp_path):
    rows = _rows(3)
    path = tmp_path / "final.csv"
    schema.write_rows_atomic(path, rows, schema.REQUIRED_COLUMNS)
    loaded = dp.load_finalized_annotations(path)
    assert len(loaded) == 3


# ---- normalization never mutates source text -------------------------------

def test_normalize_text_collapses_whitespace():
    assert dp.normalize_text("  hello   world  \n") == "hello world"


def test_prepare_classification_rows_adds_column_without_altering_original():
    rows = [make_row(comment_id="PL-1", comment_text="  spaced   text  ",
                      annotator_label="Support", annotation_confidence="2")]
    out = dp.prepare_classification_rows(rows)
    assert out[0]["comment_text"] == "  spaced   text  "  # untouched
    assert out[0]["normalized_text"] == "spaced text"  # new column only


# ---- separating labels from exclusions -------------------------------------

def test_separate_labels_and_exclusions():
    rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", exclusion_code="SPAM"),
        make_row(comment_id="PL-3"),  # pending -- neither
    ]
    labeled, excluded = dp.separate_labels_and_exclusions(rows)
    assert [r["comment_id"] for r in labeled] == ["PL-1"]
    assert [r["comment_id"] for r in excluded] == ["PL-2"]


def test_prepare_classification_rows_drops_exclusions():
    rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", exclusion_code="SPAM"),
    ]
    out = dp.prepare_classification_rows(rows)
    assert [r["comment_id"] for r in out] == ["PL-1"]


# ---- duplicate / leakage prevention ----------------------------------------

def test_duplicate_text_stays_in_one_split():
    rows = _rows(20)
    # inject a duplicate pair with identical normalized text
    dup_text = "this exact comment appears twice in the corpus"
    rows.append(make_row(comment_id="PL-DUPA", comment_text=dup_text,
                          annotator_label="Support", annotation_confidence="2"))
    rows.append(make_row(comment_id="PL-DUPB", comment_text=dup_text,
                          annotator_label="Support", annotation_confidence="2"))

    splits = dp.make_splits(rows, seed=1)
    problems = dp.verify_no_leakage(splits)
    assert problems == []

    # confirm both duplicate rows landed in the same split
    location = {}
    for name, split_rows in splits.as_dict().items():
        for r in split_rows:
            if r["comment_id"] in ("PL-DUPA", "PL-DUPB"):
                location[r["comment_id"]] = name
    assert location["PL-DUPA"] == location["PL-DUPB"]


def test_verify_no_leakage_detects_injected_text_leak():
    rows = _rows(10)
    splits = dp.make_splits(rows, seed=2)
    # Deliberately inject a leak: copy one train row into test with a new ID.
    if splits.train:
        leaked = dict(splits.train[0])
        leaked["comment_id"] = "PL-LEAK"
        splits.test.append(leaked)
    problems = dp.verify_no_leakage(splits)
    assert any("Duplicate-text leakage" in p for p in problems)


def test_verify_no_leakage_detects_id_reuse_across_splits():
    rows = _rows(10)
    splits = dp.make_splits(rows, seed=3)
    if splits.train:
        reused = dict(splits.train[0])  # same comment_id, same text
        splits.val.append(reused)
    problems = dp.verify_no_leakage(splits)
    assert any("ID leakage" in p or "Duplicate-text leakage" in p for p in problems)


# ---- stratification & reproducibility --------------------------------------

def test_splits_are_reproducible_with_same_seed():
    rows = _rows(40)
    splits_a = dp.make_splits(rows, seed=7)
    splits_b = dp.make_splits(rows, seed=7)
    ids_a = {name: sorted(r["comment_id"] for r in rs) for name, rs in splits_a.as_dict().items()}
    ids_b = {name: sorted(r["comment_id"] for r in rs) for name, rs in splits_b.as_dict().items()}
    assert ids_a == ids_b


def test_different_seeds_can_produce_different_splits():
    rows = _rows(40)
    splits_a = dp.make_splits(rows, seed=1)
    splits_b = dp.make_splits(rows, seed=999)
    ids_a = sorted(r["comment_id"] for r in splits_a.train)
    ids_b = sorted(r["comment_id"] for r in splits_b.train)
    assert ids_a != ids_b


def test_split_sizes_approximate_requested_fractions():
    rows = _rows(100)
    splits = dp.make_splits(rows, split_fractions={"train": 0.7, "val": 0.15, "test": 0.15}, seed=5)
    sizes = splits.config["split_sizes"]
    assert sizes["train"] + sizes["val"] + sizes["test"] == 100
    assert 60 <= sizes["train"] <= 80  # roughly 70%, group-level rounding allows some slack


def test_invalid_fractions_raise():
    with pytest.raises(dp.DatasetPrepError, match="must sum to 1.0"):
        dp.make_splits(_rows(5), split_fractions={"train": 0.5, "val": 0.2, "test": 0.2})


def test_empty_rows_produce_empty_splits_without_crashing():
    splits = dp.make_splits([])
    assert splits.train == [] and splits.val == [] and splits.test == []
    assert dp.verify_no_leakage(splits) == []


def test_each_stance_label_is_preserved_somewhere_across_splits():
    """All four classes present in the input must still be representable
    in the manifest's label_distribution -- no class silently vanishes."""
    rows = _rows(40)  # cycles through all four labels
    splits = dp.make_splits(rows, seed=11)
    all_labels_seen = set()
    for split_rows in splits.as_dict().values():
        all_labels_seen |= {r["annotator_label"] for r in split_rows}
    assert all_labels_seen == {"Support", "Oppose", "Neutral", "Unclear"}


# ---- manifest / reproducibility record -------------------------------------

def test_build_manifest_records_hash_and_no_training_claim(tmp_path):
    rows = _rows(10)
    path = tmp_path / "final.csv"
    schema.write_rows_atomic(path, rows, schema.REQUIRED_COLUMNS)
    splits = dp.make_splits(rows, seed=4)
    manifest = dp.build_manifest(splits, path, excluded_rows=[])

    assert manifest["source_sha256"] == schema.sha256_file(path)
    assert manifest["no_model_trained"] is True
    assert manifest["no_pseudo_labels_used"] is True
    assert manifest["gold_standard_claim"].startswith("NOT MADE")
    assert manifest["leakage_check"]["problems"] == []


def test_excluded_rows_are_counted_separately_in_manifest(tmp_path):
    rows = _rows(5) + [make_row(comment_id="PL-EX", exclusion_code="SPAM")]
    path = tmp_path / "final.csv"
    schema.write_rows_atomic(path, rows, schema.REQUIRED_COLUMNS)
    classification_rows = dp.prepare_classification_rows(rows)
    _, excluded = dp.separate_labels_and_exclusions(rows)
    splits = dp.make_splits(classification_rows, seed=6)
    manifest = dp.build_manifest(splits, path, excluded_rows=excluded)
    assert manifest["excluded_from_classification_count"] == 1


# ---- end-to-end run() -------------------------------------------------------

def test_run_end_to_end_writes_files_and_manifest(tmp_path):
    rows = _rows(30)
    source = tmp_path / "final.csv"
    schema.write_rows_atomic(source, rows, schema.REQUIRED_COLUMNS)
    output_dir = tmp_path / "splits_out"

    result = dp.run(source_path=source, output_dir=output_dir, seed=8)

    for name in ("train", "val", "test"):
        assert (output_dir / f"{name}.csv").exists()
    manifest_path = output_dir / "split_manifest.json"
    assert manifest_path.exists()
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["leakage_check"]["problems"] == []
    assert sum(manifest["config"]["split_sizes"].values()) == 30


def test_run_refuses_cleanly_when_source_missing(tmp_path):
    with pytest.raises(dp.DatasetPrepError):
        dp.run(source_path=tmp_path / "missing.csv", output_dir=tmp_path / "out")

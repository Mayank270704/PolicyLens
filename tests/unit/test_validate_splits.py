from ml.stance_classification import dataset_prep as dp
from ml.stance_classification import validate_splits as vs
from scripts.annotation import schema
from tests.unit.test_validate import make_row


def _rows(n):
    labels = ("Support", "Oppose", "Neutral", "Unclear")
    return [
        make_row(comment_id=f"PL-{i:04d}", comment_text=f"text {i}",
                 annotator_label=labels[i % 4], annotation_confidence="2",
                 annotation_notes="n" if labels[i % 4] == "Unclear" else "")
        for i in range(n)
    ]


def test_clean_split_directory_has_no_problems(tmp_path):
    rows = _rows(20)
    source = tmp_path / "final.csv"
    schema.write_rows_atomic(source, rows, schema.REQUIRED_COLUMNS)
    out_dir = tmp_path / "out"
    dp.run(source_path=source, output_dir=out_dir, seed=1)

    problems = vs.validate_split_directory(out_dir)
    assert problems == []


def test_missing_split_file_is_detected(tmp_path):
    rows = _rows(10)
    source = tmp_path / "final.csv"
    schema.write_rows_atomic(source, rows, schema.REQUIRED_COLUMNS)
    out_dir = tmp_path / "out"
    dp.run(source_path=source, output_dir=out_dir, seed=2)

    (out_dir / "test.csv").unlink()
    problems = vs.validate_split_directory(out_dir)
    assert any("Missing split file" in p for p in problems)


def test_tampered_manifest_size_mismatch_is_detected(tmp_path):
    import json
    rows = _rows(10)
    source = tmp_path / "final.csv"
    schema.write_rows_atomic(source, rows, schema.REQUIRED_COLUMNS)
    out_dir = tmp_path / "out"
    dp.run(source_path=source, output_dir=out_dir, seed=3)

    manifest_path = out_dir / "split_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["config"]["split_sizes"]["train"] += 5  # tamper
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    problems = vs.validate_split_directory(out_dir)
    assert any("does not match actual row count" in p for p in problems)


def test_exclusion_coded_row_in_a_split_file_is_rejected(tmp_path):
    rows = _rows(10)
    source = tmp_path / "final.csv"
    schema.write_rows_atomic(source, rows, schema.REQUIRED_COLUMNS)
    out_dir = tmp_path / "out"
    dp.run(source_path=source, output_dir=out_dir, seed=5)

    train_rows = schema.read_rows(out_dir / "train.csv")
    train_rows[0]["annotator_label"] = ""
    train_rows[0]["exclusion_code"] = "SPAM"
    schema.write_rows_atomic(out_dir / "train.csv", train_rows, dp.SPLIT_COLUMNS)

    problems = vs.validate_split_directory(out_dir)
    assert any("contains an excluded row" in p for p in problems)


def test_gold_standard_claim_removal_is_flagged(tmp_path):
    import json
    rows = _rows(10)
    source = tmp_path / "final.csv"
    schema.write_rows_atomic(source, rows, schema.REQUIRED_COLUMNS)
    out_dir = tmp_path / "out"
    dp.run(source_path=source, output_dir=out_dir, seed=6)

    manifest_path = out_dir / "split_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["gold_standard_claim"] = "This is gold standard."  # tampered claim
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    problems = vs.validate_split_directory(out_dir)
    assert any("gold_standard_claim" in p for p in problems)

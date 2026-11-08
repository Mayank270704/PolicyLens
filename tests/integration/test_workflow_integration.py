import json

import pytest

from scripts.annotation import finalize, schema, setup, validate
from tests.unit.test_validate import make_row


def _write(path, rows):
    schema.write_rows_atomic(path, rows, schema.REQUIRED_COLUMNS)


# ---- historical-file immutability (runs against the real repository) ----

def test_historical_and_corpus_files_match_recorded_baseline():
    """This is the project-wide guarantee the whole annotation experiment
    depends on: nothing in this workflow may ever modify the canonical
    corpus or the pre-existing historical annotation files. If
    protected_baseline.json doesn't exist yet, this test creates it from
    the current (already-verified-untouched) file contents and passes;
    on every later run it must find zero drift."""
    setup.build_protected_baseline()
    problems = setup.check_protected_baseline()
    assert problems == [], f"Protected file(s) changed since baseline: {problems}"


# ---- export integrity (Task 5) -------------------------------------------

def _complete_fixture_batch(tmp_path):
    rows = [
        make_row(comment_id="PL-1", source_dataset="dsA", word_count="3",
                 annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", source_dataset="dsA", word_count="15",
                 annotator_label="Unclear", annotation_confidence="1", annotation_notes="torn, D5"),
        make_row(comment_id="PL-3", source_dataset="dsB", word_count="30", exclusion_code="SPAM"),
    ]
    batch_path = tmp_path / "batch.csv"
    backup_path = tmp_path / "batch.original_backup.csv"
    # backup = same rows but blank labels (the pristine pre-annotation state)
    backup_rows = [
        {**r, "annotator_label": "", "exclusion_code": "", "annotation_confidence": "", "annotation_notes": ""}
        for r in rows
    ]
    _write(backup_path, backup_rows)
    _write(batch_path, rows)
    return batch_path, backup_path


def test_finalize_succeeds_on_a_fully_annotated_batch(tmp_path):
    batch_path, backup_path = _complete_fixture_batch(tmp_path)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"repeat_subset_comment_ids": []}), encoding="utf-8")
    repeat_batch_path = tmp_path / "repeat_pass_batch.csv"  # does not exist -- fine, no repeat ids
    output_csv = tmp_path / "finalized" / "final.csv"
    report_path = tmp_path / "finalized" / "report.json"

    report = finalize.run_finalize(
        batch_path=batch_path, backup_path=backup_path, plan_path=plan_path,
        repeat_batch_path=repeat_batch_path, output_csv_path=output_csv, report_path=report_path,
    )

    assert report["row_count"] == 3
    assert report["labeled_count"] == 2
    assert report["excluded_count"] == 1
    assert report["stance_distribution"] == {"Support": 1, "Unclear": 1}
    assert report["exclusion_distribution"] == {"SPAM": 1}
    assert report["validation"]["errors"] == 0
    assert output_csv.exists()
    assert report_path.exists()
    assert report["gold_standard_claim"].startswith("NOT MADE")


def test_finalize_does_not_modify_the_source_batch(tmp_path):
    batch_path, backup_path = _complete_fixture_batch(tmp_path)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"repeat_subset_comment_ids": []}), encoding="utf-8")
    repeat_batch_path = tmp_path / "repeat_pass_batch.csv"
    output_csv = tmp_path / "finalized" / "final.csv"
    report_path = tmp_path / "finalized" / "report.json"

    before_hash = schema.sha256_file(batch_path)
    finalize.run_finalize(
        batch_path=batch_path, backup_path=backup_path, plan_path=plan_path,
        repeat_batch_path=repeat_batch_path, output_csv_path=output_csv, report_path=report_path,
    )
    after_hash = schema.sha256_file(batch_path)
    assert before_hash == after_hash


def test_finalize_refuses_when_batch_incomplete(tmp_path):
    rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2"),  # pending
    ]
    backup_rows = [{**r, "annotator_label": "", "exclusion_code": ""} for r in rows]
    batch_path = tmp_path / "batch.csv"
    backup_path = tmp_path / "batch.original_backup.csv"
    _write(batch_path, rows)
    _write(backup_path, backup_rows)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"repeat_subset_comment_ids": []}), encoding="utf-8")

    with pytest.raises(finalize.FinalizationError, match="incomplete"):
        finalize.run_finalize(
            batch_path=batch_path, backup_path=backup_path, plan_path=plan_path,
            repeat_batch_path=tmp_path / "no_such_file.csv",
            output_csv_path=tmp_path / "out.csv", report_path=tmp_path / "report.json",
        )
    assert not (tmp_path / "out.csv").exists()


def test_finalize_refuses_when_text_was_edited_after_generation(tmp_path):
    batch_path, backup_path = _complete_fixture_batch(tmp_path)
    rows = schema.read_rows(batch_path)
    rows[0]["comment_text"] = "This was edited by hand after the batch was generated."
    schema.write_rows_atomic(batch_path, rows, schema.REQUIRED_COLUMNS)

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"repeat_subset_comment_ids": []}), encoding="utf-8")

    with pytest.raises(finalize.FinalizationError, match="Validation failed"):
        finalize.run_finalize(
            batch_path=batch_path, backup_path=backup_path, plan_path=plan_path,
            repeat_batch_path=tmp_path / "no_such_file.csv",
            output_csv_path=tmp_path / "out.csv", report_path=tmp_path / "report.json",
        )


def test_finalize_refuses_without_a_backup_file(tmp_path):
    rows = [make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3")]
    batch_path = tmp_path / "batch.csv"
    _write(batch_path, rows)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"repeat_subset_comment_ids": []}), encoding="utf-8")

    with pytest.raises(finalize.FinalizationError, match="No original backup"):
        finalize.run_finalize(
            batch_path=batch_path, backup_path=tmp_path / "missing_backup.csv", plan_path=plan_path,
            repeat_batch_path=tmp_path / "no_such_file.csv",
            output_csv_path=tmp_path / "out.csv", report_path=tmp_path / "report.json",
        )


def test_finalize_accounts_for_the_full_original_sample(tmp_path):
    """If a row was ever dropped between backup and working file, finalize
    must refuse rather than silently exporting a partial dataset."""
    rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", annotator_label="Oppose", annotation_confidence="3"),
    ]
    backup_rows = [{**r, "annotator_label": "", "exclusion_code": ""} for r in rows]
    batch_path = tmp_path / "batch.csv"
    backup_path = tmp_path / "backup.csv"
    _write(backup_path, backup_rows)
    _write(batch_path, rows[:1])  # one row silently dropped

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"repeat_subset_comment_ids": []}), encoding="utf-8")

    with pytest.raises(finalize.FinalizationError):
        finalize.run_finalize(
            batch_path=batch_path, backup_path=backup_path, plan_path=plan_path,
            repeat_batch_path=tmp_path / "no_such_file.csv",
            output_csv_path=tmp_path / "out.csv", report_path=tmp_path / "report.json",
        )


# ---- end-to-end wiring: validate -> progress -> finalize -----------------

def test_full_pipeline_on_the_real_generated_batch_is_internally_consistent():
    """Sanity-check the actual annotation_batch_001.csv shipped in this
    repo (still blank at this point in the project): schema valid,
    deterministic row count of 250, and immutability check passes against
    its own backup."""
    fieldnames, rows = schema.read_rows_with_fieldnames(schema.MAIN_BATCH_PATH)
    assert len(rows) == 250
    backup_rows = schema.read_rows(schema.MAIN_BATCH_BACKUP_PATH)
    issues = validate.validate_batch(rows, fieldnames=fieldnames, backup_rows=backup_rows)
    errors = [i for i in issues if i.severity == "ERROR"]
    assert errors == []

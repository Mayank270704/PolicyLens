import json
from datetime import datetime, timedelta, timezone

from scripts.annotation import evaluate, schema, timing
from tests.unit.test_validate import make_row


def _ts(base, offset_seconds):
    return (base + timedelta(seconds=offset_seconds)).isoformat()


def test_timing_no_data_is_handled_without_crashing():
    report = timing.analyze_timing([])
    assert report["status"] == "no_data"
    assert "limitations" in report


def test_timing_computes_active_time_between_saves():
    base = datetime(2026, 11, 1, tzinfo=timezone.utc)
    events = [
        {"timestamp_utc": _ts(base, 0), "batch_file": "b.csv", "comment_id": "PL-1", "action": "saved"},
        {"timestamp_utc": _ts(base, 30), "batch_file": "b.csv", "comment_id": "PL-2", "action": "saved"},
        {"timestamp_utc": _ts(base, 90), "batch_file": "b.csv", "comment_id": "PL-3", "action": "saved"},
    ]
    report = timing.analyze_timing(events)
    assert report["status"] == "ok"
    assert report["n_save_events"] == 3
    # two gaps: 30s and 60s
    assert report["active_time_per_item_seconds"]["median"] == 45.0


def test_timing_excludes_long_gaps_as_breaks():
    base = datetime(2026, 11, 1, tzinfo=timezone.utc)
    events = [
        {"timestamp_utc": _ts(base, 0), "batch_file": "b.csv", "comment_id": "PL-1", "action": "saved"},
        {"timestamp_utc": _ts(base, 20), "batch_file": "b.csv", "comment_id": "PL-2", "action": "saved"},
        # a 2-hour gap -- a real break, not active annotation time
        {"timestamp_utc": _ts(base, 20 + 7200), "batch_file": "b.csv", "comment_id": "PL-3", "action": "saved"},
    ]
    report = timing.analyze_timing(events, break_threshold_seconds=600)
    assert report["n_gaps_classified_as_breaks"] == 1
    assert report["n_items_with_active_time_estimate"] == 1
    assert report["active_time_per_item_seconds"]["median"] == 20.0


def test_timing_excludes_overwrite_resaves_from_fresh_item_timing():
    base = datetime(2026, 11, 1, tzinfo=timezone.utc)
    events = [
        {"timestamp_utc": _ts(base, 0), "batch_file": "b.csv", "comment_id": "PL-1", "action": "saved"},
        {"timestamp_utc": _ts(base, 10), "batch_file": "b.csv", "comment_id": "PL-1", "action": "overwrite"},
        {"timestamp_utc": _ts(base, 50), "batch_file": "b.csv", "comment_id": "PL-2", "action": "saved"},
    ]
    report = timing.analyze_timing(events)
    # the overwrite gap (10s) must be excluded; only the 40s gap (overwrite -> PL-2) counts... but
    # the gap INTO an overwrite save is also excluded since is_fresh_item is based on the *current*
    # event's action. Here: gap1 (0->10) lands on an overwrite event -> excluded.
    # gap2 (10->50, 40s) lands on a fresh 'saved' event -> included.
    assert report["n_items_with_active_time_estimate"] == 1
    assert report["active_time_per_item_seconds"]["median"] == 40.0


def test_timing_low_sample_warning_below_ten_items():
    base = datetime(2026, 11, 1, tzinfo=timezone.utc)
    events = [
        {"timestamp_utc": _ts(base, i * 10), "batch_file": "b.csv", "comment_id": f"PL-{i}", "action": "saved"}
        for i in range(3)
    ]
    report = timing.analyze_timing(events)
    assert "low_sample_warning" in report


# ---- consolidated evaluate report -------------------------------------

def test_evaluate_handles_a_completely_blank_batch(tmp_path):
    rows = [make_row(comment_id=f"PL-{i}") for i in range(5)]
    batch_path = tmp_path / "batch.csv"
    schema.write_rows_atomic(batch_path, rows, schema.REQUIRED_COLUMNS)

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"repeat_subset_comment_ids": []}), encoding="utf-8")

    report = evaluate.build_full_report(
        batch_path=batch_path,
        repeat_batch_path=tmp_path / "no_repeat.csv",
        plan_path=plan_path,
        events_path=tmp_path / "no_events.csv",
    )

    assert report["annotation_progress"]["pending_comments"] == 5
    assert report["intra_annotator_consistency"]["status"] in (
        "first_pass_incomplete", "second_pass_incomplete",
    )
    assert report["annotation_timing"]["status"] == "no_data"
    # format_report must not crash on the "no data yet" states
    text = evaluate.format_report(report)
    assert "Annotation progress" in text


def test_evaluate_reports_computed_kappa_once_both_passes_exist(tmp_path):
    rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", annotator_label="Oppose", annotation_confidence="2"),
    ]
    batch_path = tmp_path / "batch.csv"
    schema.write_rows_atomic(batch_path, rows, schema.REQUIRED_COLUMNS)

    repeat_rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", annotator_label="Oppose", annotation_confidence="2"),
    ]
    repeat_path = tmp_path / "repeat.csv"
    schema.write_rows_atomic(repeat_path, repeat_rows, schema.REQUIRED_COLUMNS)

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps({"repeat_subset_comment_ids": ["PL-1", "PL-2"]}), encoding="utf-8")

    report = evaluate.build_full_report(
        batch_path=batch_path, repeat_batch_path=repeat_path, plan_path=plan_path,
        events_path=tmp_path / "no_events.csv",
    )
    assert report["intra_annotator_consistency"]["status"] == "computed"
    assert report["intra_annotator_consistency"]["stance_kappa"]["kappa"] == 1.0
    assert "low_sample_warning" in report["intra_annotator_consistency"]["stance_kappa"]

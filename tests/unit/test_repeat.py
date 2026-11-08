import json
from datetime import datetime, timedelta, timezone

import pytest

from scripts.annotation import repeat, schema, state
from tests.unit.test_validate import make_row


# ---- Cohen's kappa -------------------------------------------------------

def test_kappa_is_one_for_perfect_agreement():
    labels = ["Support", "Oppose", "Neutral", "Unclear", "Support"]
    k = repeat.cohens_kappa(labels, labels, schema.STANCE_LABELS)
    assert k == 1.0


def test_kappa_is_less_than_one_for_partial_disagreement():
    pass1 = ["Support", "Oppose", "Neutral", "Unclear"]
    pass2 = ["Support", "Oppose", "Neutral", "Support"]
    k = repeat.cohens_kappa(pass1, pass2, schema.STANCE_LABELS)
    assert k is not None
    assert k < 1.0


def test_kappa_none_for_empty_input():
    assert repeat.cohens_kappa([], [], schema.STANCE_LABELS) is None


def test_kappa_mismatched_lengths_returns_none():
    assert repeat.cohens_kappa(["Support"], ["Support", "Oppose"], schema.STANCE_LABELS) is None


@pytest.mark.parametrize("k,expected", [
    (-0.1, "no agreement"),
    (0.1, "slight"),
    (0.3, "fair"),
    (0.5, "moderate"),
    (0.7, "substantial"),
    (0.95, "almost perfect"),
    (None, "undefined (no comparable items)"),
])
def test_kappa_interpretation_bands(k, expected):
    assert repeat.interpret_kappa(k) == expected


# ---- consistency report: confusion matrix + exclusion agreement ---------

def _write_batch(path, rows):
    schema.write_rows_atomic(path, rows, schema.REQUIRED_COLUMNS)


def test_compute_consistency_report_fixture_only(tmp_path):
    """Uses fixture files only -- this test never generates a real second
    annotation round, it only exercises the computation on fabricated
    test data that is explicitly fixture material, not a claim about any
    real annotator's actual second pass."""
    plan = {
        "repeat_subset_comment_ids": ["PL-1", "PL-2", "PL-3", "PL-4"],
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    main_rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", annotator_label="Oppose", annotation_confidence="2"),
        make_row(comment_id="PL-3", exclusion_code="SPAM"),
        make_row(comment_id="PL-4", annotator_label="Neutral", annotation_confidence="2"),
    ]
    repeat_rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", annotator_label="Neutral", annotation_confidence="2"),  # disagree
        make_row(comment_id="PL-3", exclusion_code="SPAM"),  # agree on exclusion
        make_row(comment_id="PL-4", annotator_label="Neutral", annotation_confidence="3"),
    ]

    main_path = tmp_path / "main.csv"
    repeat_path = tmp_path / "repeat.csv"
    _write_batch(main_path, main_rows)
    _write_batch(repeat_path, repeat_rows)

    report = repeat.compute_consistency_report(main_path, repeat_path, plan_path)

    assert report["exclusion_agreement"]["agreement_rate"] == 1.0  # all 4 agree excluded/not-excluded
    assert report["stance_kappa"]["n_items_compared"] == 3  # PL-3 excluded from kappa
    assert report["confusion_matrix"]["Support"]["Support"] == 1
    assert report["confusion_matrix"]["Oppose"]["Neutral"] == 1
    assert report["confusion_matrix"]["Neutral"]["Neutral"] == 1
    assert report["class_wise_agreement"]["Oppose"]["agreement_rate"] == 0.0
    assert report["class_wise_agreement"]["Support"]["agreement_rate"] == 1.0


def test_compute_consistency_report_refuses_when_first_pass_incomplete(tmp_path):
    plan = {"repeat_subset_comment_ids": ["PL-1", "PL-2"]}
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    main_rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2"),  # pending -- first pass not complete
    ]
    repeat_rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", annotator_label="Support", annotation_confidence="3"),
    ]
    main_path = tmp_path / "main.csv"
    repeat_path = tmp_path / "repeat.csv"
    _write_batch(main_path, main_rows)
    _write_batch(repeat_path, repeat_rows)

    with pytest.raises(RuntimeError, match="First pass incomplete"):
        repeat.compute_consistency_report(main_path, repeat_path, plan_path)


def test_compute_consistency_report_refuses_when_second_pass_missing(tmp_path):
    """Must never fabricate a second round: if the repeat-pass file does
    not exist yet, refuse outright rather than inventing labels."""
    plan = {"repeat_subset_comment_ids": ["PL-1"]}
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    main_rows = [make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3")]
    main_path = tmp_path / "main.csv"
    _write_batch(main_path, main_rows)

    repeat_path = tmp_path / "does_not_exist.csv"

    with pytest.raises(RuntimeError, match="Second pass is not complete"):
        repeat.compute_consistency_report(main_path, repeat_path, plan_path)


def test_compute_consistency_report_refuses_when_second_pass_partial(tmp_path):
    plan = {"repeat_subset_comment_ids": ["PL-1", "PL-2"]}
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    main_rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", annotator_label="Oppose", annotation_confidence="2"),
    ]
    repeat_rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2"),  # still pending in round 2
    ]
    main_path = tmp_path / "main.csv"
    repeat_path = tmp_path / "repeat.csv"
    _write_batch(main_path, main_rows)
    _write_batch(repeat_path, repeat_rows)

    with pytest.raises(RuntimeError, match="Second pass is not complete"):
        repeat.compute_consistency_report(main_path, repeat_path, plan_path)


# ---- repeat-batch preparation: blinding + the 14-day gate ----------------

def test_prepare_repeat_batch_strips_labels(tmp_path, monkeypatch):
    monkeypatch.setattr(schema, "STATE_PATH", tmp_path / "state.json")

    main_path = tmp_path / "main.csv"
    plan_path = tmp_path / "plan.json"
    out_path = tmp_path / "repeat_out.csv"

    rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3",
                  annotation_notes="clear support"),
        make_row(comment_id="PL-2", annotator_label="Oppose", annotation_confidence="2"),
    ]
    _write_batch(main_path, rows)
    plan_path.write_text(json.dumps({"repeat_subset_comment_ids": ["PL-1", "PL-2"]}), encoding="utf-8")

    # Open the gate: mark main batch complete 20 days ago.
    old_ts = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
    state.save_state({"batches": {"main.csv": {"last_index": 0, "completed_utc": old_ts}}})

    out = repeat.prepare_repeat_batch(main_path, plan_path, out_path)
    assert out == out_path

    produced = schema.read_rows(out_path)
    assert {r["comment_id"] for r in produced} == {"PL-1", "PL-2"}
    for r in produced:
        assert r["annotator_label"] == ""
        assert r["exclusion_code"] == ""
        assert r["annotation_confidence"] == ""
        assert r["annotation_notes"] == ""
        # comment text/metadata must still be present (not stripped, just labels)
        assert r["comment_text"]


def test_prepare_repeat_batch_blocked_before_gate_opens(tmp_path, monkeypatch):
    monkeypatch.setattr(schema, "STATE_PATH", tmp_path / "state.json")

    main_path = tmp_path / "main.csv"
    plan_path = tmp_path / "plan.json"
    out_path = tmp_path / "repeat_out.csv"

    rows = [make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3")]
    _write_batch(main_path, rows)
    plan_path.write_text(json.dumps({"repeat_subset_comment_ids": ["PL-1"]}), encoding="utf-8")

    # Mark complete just now -- gate should NOT be open yet.
    state.save_state({"batches": {"main.csv": {"last_index": 0, "completed_utc": schema.utcnow_iso()}}})

    with pytest.raises(RuntimeError, match="Repeat gate not open yet"):
        repeat.prepare_repeat_batch(main_path, plan_path, out_path)
    assert not out_path.exists()


def test_prepare_repeat_batch_blocked_if_main_batch_never_completed(tmp_path, monkeypatch):
    monkeypatch.setattr(schema, "STATE_PATH", tmp_path / "state.json")
    main_path = tmp_path / "main.csv"
    plan_path = tmp_path / "plan.json"
    out_path = tmp_path / "repeat_out.csv"
    rows = [make_row(comment_id="PL-1")]  # pending, never completed
    _write_batch(main_path, rows)
    plan_path.write_text(json.dumps({"repeat_subset_comment_ids": ["PL-1"]}), encoding="utf-8")

    with pytest.raises(RuntimeError, match="not yet 100% annotated"):
        repeat.prepare_repeat_batch(main_path, plan_path, out_path)


def test_prepare_repeat_batch_refuses_to_clobber_existing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(schema, "STATE_PATH", tmp_path / "state.json")
    main_path = tmp_path / "main.csv"
    plan_path = tmp_path / "plan.json"
    out_path = tmp_path / "repeat_out.csv"

    rows = [make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3")]
    _write_batch(main_path, rows)
    plan_path.write_text(json.dumps({"repeat_subset_comment_ids": ["PL-1"]}), encoding="utf-8")
    out_path.write_text("already here", encoding="utf-8")

    old_ts = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
    state.save_state({"batches": {"main.csv": {"last_index": 0, "completed_utc": old_ts}}})

    with pytest.raises(FileExistsError):
        repeat.prepare_repeat_batch(main_path, plan_path, out_path)

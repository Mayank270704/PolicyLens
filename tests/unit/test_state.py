from scripts.annotation import schema, state
from tests.unit.test_validate import make_row


def _patch_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(schema, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(schema, "AUDIT_LOG_PATH", tmp_path / "audit_log.csv")
    monkeypatch.setattr(schema, "TIMING_LOG_PATH", tmp_path / "annotation_events.csv")


# ---- save/resume behavior -------------------------------------------------

def test_last_index_defaults_to_zero(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch_path = tmp_path / "batch.csv"
    assert state.get_last_index(batch_path) == 0


def test_last_index_round_trips(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch_path = tmp_path / "batch.csv"
    state.set_last_index(batch_path, 42)
    assert state.get_last_index(batch_path) == 42


def test_last_index_is_tracked_independently_per_batch_file(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch_a = tmp_path / "a.csv"
    batch_b = tmp_path / "b.csv"
    state.set_last_index(batch_a, 5)
    state.set_last_index(batch_b, 9)
    assert state.get_last_index(batch_a) == 5
    assert state.get_last_index(batch_b) == 9


# ---- completion tracking (gates the repeat-annotation wait) --------------

def test_mark_complete_if_needed_false_while_pending(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch_path = tmp_path / "batch.csv"
    rows = [make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
            make_row(comment_id="PL-2")]
    assert state.mark_complete_if_needed(batch_path, rows) is False
    assert state.get_completed_utc(batch_path) is None


def test_mark_complete_if_needed_true_once_all_rows_done(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch_path = tmp_path / "batch.csv"
    rows = [make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
            make_row(comment_id="PL-2", exclusion_code="SPAM")]
    assert state.mark_complete_if_needed(batch_path, rows) is True
    assert state.get_completed_utc(batch_path) is not None


def test_mark_complete_if_needed_does_not_overwrite_existing_timestamp(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch_path = tmp_path / "batch.csv"
    rows = [make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3")]
    assert state.mark_complete_if_needed(batch_path, rows) is True
    first_ts = state.get_completed_utc(batch_path)
    assert state.mark_complete_if_needed(batch_path, rows) is False
    assert state.get_completed_utc(batch_path) == first_ts


# ---- audit log for overwritten annotations --------------------------------

def test_append_audit_entry_creates_header_once(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch_path = tmp_path / "batch.csv"
    state.append_audit_entry(batch_path, "PL-1", "Support", "", "Oppose", "")
    state.append_audit_entry(batch_path, "PL-2", "", "", "Neutral", "")

    content = schema.AUDIT_LOG_PATH.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if l.strip()]
    assert lines[0].startswith("timestamp_utc,")
    assert len(lines) == 3  # header + 2 entries
    assert "PL-1" in lines[1]
    assert "PL-2" in lines[2]


# ---- timing event log -------------------------------------------------------

def test_append_timing_event_creates_header_once(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    batch_path = tmp_path / "batch.csv"
    state.append_timing_event(batch_path, "PL-1", action="saved")
    state.append_timing_event(batch_path, "PL-2", action="overwrite")

    content = schema.TIMING_LOG_PATH.read_text(encoding="utf-8")
    lines = [l for l in content.splitlines() if l.strip()]
    assert lines[0].startswith("timestamp_utc,")
    assert len(lines) == 3
    assert "PL-1,saved" in lines[1]
    assert "PL-2,overwrite" in lines[2]


# ---- backup creation -------------------------------------------------------

def test_ensure_backup_creates_copy_when_missing(tmp_path):
    batch_path = tmp_path / "batch.csv"
    backup_path = tmp_path / "batch.original_backup.csv"
    rows = [make_row(comment_id="PL-1")]
    schema.write_rows_atomic(batch_path, rows, schema.REQUIRED_COLUMNS)

    created = state.ensure_backup(batch_path, backup_path)
    assert created is True
    assert backup_path.exists()
    assert schema.read_rows(backup_path) == schema.read_rows(batch_path)


def test_ensure_backup_never_overwrites_existing_backup(tmp_path):
    batch_path = tmp_path / "batch.csv"
    backup_path = tmp_path / "batch.original_backup.csv"
    schema.write_rows_atomic(batch_path, [make_row(comment_id="PL-1")], schema.REQUIRED_COLUMNS)
    state.ensure_backup(batch_path, backup_path)

    # Now "annotate" the working file -- backup must stay untouched.
    schema.write_rows_atomic(
        batch_path,
        [make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3")],
        schema.REQUIRED_COLUMNS,
    )
    created_again = state.ensure_backup(batch_path, backup_path)
    assert created_again is False
    backup_rows = schema.read_rows(backup_path)
    assert backup_rows[0]["annotator_label"] == ""

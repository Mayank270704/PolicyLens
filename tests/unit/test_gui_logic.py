"""GUI logic tests. These exercise AnnotationApp's save/resume/filter/clear
behavior directly (no simulated clicks), skipped automatically in a headless
environment where Tkinter can't open a window."""
import tkinter as tk

import pytest

from scripts.annotation import gui, schema, state
from tests.unit.test_validate import make_row


def _write_batch(path, rows):
    schema.write_rows_atomic(path, rows, schema.REQUIRED_COLUMNS)


@pytest.fixture(scope="session")
def tk_session_root():
    """One real Tk interpreter for the whole test session. Repeatedly
    creating and destroying top-level Tk() interpreters (one per test) was
    observed to be flaky on this machine -- intermittent TclError on
    creation under rapid create/destroy cycles. Each test instead gets its
    own Toplevel under this single long-lived interpreter, which is cheap
    and reliable to create/destroy per test."""
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        pytest.skip("No display available for Tkinter in this environment.")
        return
    yield root
    root.destroy()


@pytest.fixture
def tk_root(tk_session_root):
    win = tk.Toplevel(tk_session_root)
    win.withdraw()
    yield win
    win.destroy()


@pytest.fixture(autouse=True)
def no_blocking_dialogs(monkeypatch):
    """Every messagebox call in gui.py must be patched by default in tests,
    never left to open a real modal window -- a real showinfo/showerror
    dialog blocks waiting for a human click and hangs the test process
    indefinitely in a non-interactive run. Individual tests can still
    override askyesno/askyesnocancel to exercise a specific user choice."""
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *a, **k: None)
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *a, **k: None)
    monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *a, **k: True)
    monkeypatch.setattr("tkinter.messagebox.askyesnocancel", lambda *a, **k: True)


@pytest.fixture
def app_factory(tmp_path, monkeypatch, tk_root):
    monkeypatch.setattr(schema, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(schema, "AUDIT_LOG_PATH", tmp_path / "audit_log.csv")
    monkeypatch.setattr(schema, "TIMING_LOG_PATH", tmp_path / "annotation_events.csv")

    def make(rows):
        batch_path = tmp_path / "batch.csv"
        backup_path = tmp_path / "batch.original_backup.csv"
        _write_batch(batch_path, rows)
        return gui.AnnotationApp(tk_root, batch_path, backup_path), batch_path, backup_path

    return make


def _rows(n=4):
    return [make_row(comment_id=f"PL-{i}", comment_text=f"text {i}", word_count="2") for i in range(n)]


# ---- save/resume -----------------------------------------------------------

def test_save_persists_to_disk_immediately(app_factory):
    app, batch_path, _ = app_factory(_rows())
    app.stance_var.set("Support")
    app.confidence_var.set("3")
    assert app._save_current(advance=False) is True

    on_disk = schema.read_rows(batch_path)
    assert on_disk[0]["annotator_label"] == "Support"
    assert on_disk[0]["annotation_confidence"] == "3"


def test_resume_picks_up_last_index(app_factory, tmp_path, tk_session_root):
    app, batch_path, _ = app_factory(_rows())
    app._jump_to_row_index(2)
    assert state.get_last_index(batch_path) == 2

    # Simulate reopening: a fresh AnnotationApp instance against the same
    # batch/state should resume at index 2, not restart at 0.
    win2 = tk.Toplevel(tk_session_root)
    win2.withdraw()
    try:
        app2 = gui.AnnotationApp(win2, batch_path, app.backup_path)
        assert app2.current_row_index == 2
    finally:
        win2.destroy()


def test_closing_with_unsaved_changes_does_not_silently_lose_data(app_factory, monkeypatch):
    """Simulates answering 'No' (discard) to the unsaved-changes prompt:
    the in-memory dirty flag must be cleared without writing the bad
    in-progress edit to disk, and the file on disk must be unaffected."""
    app, batch_path, _ = app_factory(_rows())
    before = schema.read_rows(batch_path)

    app.stance_var.set("Oppose")  # unsaved edit
    assert app.dirty is True

    monkeypatch.setattr("tkinter.messagebox.askyesnocancel", lambda *a, **k: False)  # "No" = discard
    assert app._confirm_discard_if_dirty() is True
    assert app.dirty is False

    after = schema.read_rows(batch_path)
    assert after == before  # nothing was written


def test_closing_with_unsaved_changes_can_save_via_prompt(app_factory, monkeypatch):
    app, batch_path, _ = app_factory(_rows())
    app.stance_var.set("Neutral")
    app.confidence_var.set("2")

    monkeypatch.setattr("tkinter.messagebox.askyesnocancel", lambda *a, **k: True)  # "Yes" = save
    assert app._confirm_discard_if_dirty() is True

    after = schema.read_rows(batch_path)
    assert after[0]["annotator_label"] == "Neutral"


# ---- repeated saves preserve integrity ------------------------------------

def test_repeated_saves_do_not_corrupt_other_rows(app_factory):
    app, batch_path, _ = app_factory(_rows(5))

    for i in range(5):
        app._load_row(i)
        app.stance_var.set("Support")
        app.confidence_var.set("3")
        assert app._save_current(advance=False) is True

    rows = schema.read_rows(batch_path)
    assert len(rows) == 5
    assert all(r["annotator_label"] == "Support" for r in rows)
    # comment_text for each row must be exactly what it started as
    assert [r["comment_text"] for r in rows] == [f"text {i}" for i in range(5)]


def test_overwrite_is_confirmed_and_audited(app_factory, monkeypatch):
    app, batch_path, _ = app_factory(_rows(1))
    app.stance_var.set("Support")
    app.confidence_var.set("3")
    app._save_current(advance=False)

    app.stance_var.set("Oppose")  # change the label on an already-saved item
    app.confidence_var.set("2")
    monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *a, **k: True)  # confirm overwrite
    app._save_current(advance=False)

    rows = schema.read_rows(batch_path)
    assert rows[0]["annotator_label"] == "Oppose"
    audit_content = schema.AUDIT_LOG_PATH.read_text(encoding="utf-8")
    assert "Support" in audit_content and "Oppose" in audit_content


def test_overwrite_declined_keeps_original_label(app_factory, monkeypatch):
    app, batch_path, _ = app_factory(_rows(1))
    app.stance_var.set("Support")
    app.confidence_var.set("3")
    app._save_current(advance=False)

    app.stance_var.set("Oppose")
    monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *a, **k: False)  # decline overwrite
    result = app._save_current(advance=False)
    assert result is False

    rows = schema.read_rows(batch_path)
    assert rows[0]["annotator_label"] == "Support"  # unchanged on disk


# ---- clear-annotation ------------------------------------------------------

def test_clear_resets_fields_but_requires_explicit_save(app_factory, monkeypatch):
    app, batch_path, _ = app_factory(_rows(1))
    app.stance_var.set("Support")
    app.confidence_var.set("3")
    app.notes_text.insert("1.0", "some note")
    app._save_current(advance=False)

    monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *a, **k: True)
    app._clear_current_fields()
    assert app.stance_var.get() == ""
    assert app.confidence_var.get() == ""
    assert app.notes_text.get("1.0", "end").strip() == ""

    # not yet written to disk until Save is clicked
    assert schema.read_rows(batch_path)[0]["annotator_label"] == "Support"

    app._save_current(advance=False)
    assert schema.read_rows(batch_path)[0]["annotator_label"] == ""


# ---- filtered navigation stays live after a save --------------------------

def test_filtered_list_refreshes_after_save_changes_item_status(app_factory):
    rows = _rows(3)
    app, batch_path, _ = app_factory(rows)

    app.filter_var.set(gui.FILTER_PENDING)
    app._apply_filter()
    assert len(app.filtered_indices) == 3  # all pending initially

    app.stance_var.set("Support")
    app.confidence_var.set("3")
    app._save_current(advance=False)

    # The just-saved item is no longer Pending, so the Pending filter list
    # must shrink immediately, not stay stale at 3 items.
    assert len(app.filtered_indices) == 2
    assert app.current_row_index not in app.filtered_indices


def test_filtered_list_falls_back_to_all_when_filter_becomes_empty(app_factory):
    app, batch_path, _ = app_factory(_rows(1))
    app.filter_var.set(gui.FILTER_PENDING)
    app._apply_filter()

    app.stance_var.set("Support")
    app.confidence_var.set("3")
    app._save_current(advance=False)

    assert app.filter_var.get() == gui.FILTER_ALL
    assert app.filtered_indices == [0]

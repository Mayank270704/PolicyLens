import csv
import io

from backend.app.models.comment import Comment
from backend.app.models.import_log import ImportRun
from backend.app.models.policy import PolicyDocument
from backend.app.services.bulk_export import export_comments_csv
from backend.app.services.bulk_import import import_comments_csv


def _policy(db_session, title="P"):
    p = PolicyDocument(title=title)
    db_session.add(p)
    db_session.commit()
    return p


def _rows(n, source_dataset="synthetic"):
    return [
        {"original_text": f"Synthetic comment number {i} about the policy.",
         "source_dataset": source_dataset, "source_record_id": str(i), "language": "English"}
        for i in range(n)
    ]


# ---- basic import -----------------------------------------------------------

def test_import_creates_comments(db_session):
    policy = _policy(db_session)
    report = import_comments_csv(db_session, policy.id, _rows(5), source_label="test.csv")
    assert report.total_rows == 5
    assert report.created_count == 5
    assert report.error_count == 0

    comments = db_session.query(Comment).filter_by(policy_document_id=policy.id).all()
    assert len(comments) == 5


def test_import_run_is_persisted_as_audit_log(db_session):
    policy = _policy(db_session)
    report = import_comments_csv(db_session, policy.id, _rows(3), source_label="audit_test.csv")
    run = db_session.get(ImportRun, report.import_run_id)
    assert run is not None
    assert run.import_type == "comment_csv"
    assert run.source_label == "audit_test.csv"
    assert run.created_count == 3
    assert run.completed_at is not None


# ---- schema validation / error reporting ------------------------------------

def test_missing_required_column_is_an_error_not_a_crash(db_session):
    policy = _policy(db_session)
    rows = [{"original_text": "ok comment", "source_dataset": "x"}]  # missing source_record_id
    report = import_comments_csv(db_session, policy.id, rows, source_label="bad.csv")
    assert report.error_count == 1
    assert report.created_count == 0
    assert "source_record_id" in report.errors[0].message


def test_one_bad_row_does_not_abort_the_rest(db_session):
    policy = _policy(db_session)
    rows = _rows(3)
    rows.insert(1, {"original_text": "", "source_dataset": "x", "source_record_id": "bad"})  # blank text
    report = import_comments_csv(db_session, policy.id, rows, source_label="mixed.csv")
    assert report.total_rows == 4
    assert report.error_count == 1
    assert report.created_count == 3


def test_error_report_never_includes_full_comment_text(db_session):
    policy = _policy(db_session)
    long_text_missing_source = {"original_text": "x" * 500, "source_dataset": "", "source_record_id": "1"}
    report = import_comments_csv(db_session, policy.id, [long_text_missing_source], source_label="t.csv")
    assert report.error_count == 1
    assert len(report.errors[0].text_snippet) <= 80


# ---- duplicate detection: two kinds, kept distinct --------------------------

def test_identical_text_different_source_record_increments_multiplicity(db_session):
    policy = _policy(db_session)
    rows = [
        {"original_text": "Exactly the same text.", "source_dataset": "a", "source_record_id": "1"},
        {"original_text": "Exactly the same text.", "source_dataset": "a", "source_record_id": "2"},
    ]
    report = import_comments_csv(db_session, policy.id, rows, source_label="dup.csv")
    assert report.created_count == 1
    assert report.incremented_count == 1
    comments = db_session.query(Comment).filter_by(policy_document_id=policy.id).all()
    assert len(comments) == 1
    assert comments[0].multiplicity == 2


def test_reimporting_the_same_file_is_idempotent(db_session):
    """Re-running the identical import (same source_dataset +
    source_record_id per row) must not double-count anything -- this is
    the KEY distinction from the multiplicity-increment path above."""
    policy = _policy(db_session)
    rows = _rows(3)
    report1 = import_comments_csv(db_session, policy.id, rows, source_label="run1.csv")
    report2 = import_comments_csv(db_session, policy.id, rows, source_label="run2.csv")

    assert report1.created_count == 3
    assert report2.created_count == 0
    assert report2.skipped_already_imported_count == 3

    comments = db_session.query(Comment).filter_by(policy_document_id=policy.id).all()
    assert len(comments) == 3
    assert all(c.multiplicity == 1 for c in comments)  # NOT incremented by the idempotent re-import


# ---- batch processing --------------------------------------------------------

def test_large_import_processes_in_batches_without_error(db_session):
    policy = _policy(db_session)
    report = import_comments_csv(db_session, policy.id, _rows(50), source_label="big.csv", batch_size=10)
    assert report.created_count == 50
    assert report.error_count == 0


# ---- export -------------------------------------------------------------------

def test_export_round_trips_via_csv(db_session):
    policy = _policy(db_session)
    import_comments_csv(db_session, policy.id, _rows(3), source_label="e.csv")
    csv_text = export_comments_csv(db_session, policy.id)
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) == 3
    assert all(r["original_text"].startswith("Synthetic comment") for r in rows)
    assert all(r["latest_stance_label"] == "" for r in rows)  # no stance predictions yet


def test_export_empty_policy_produces_header_only(db_session):
    policy = _policy(db_session)
    csv_text = export_comments_csv(db_session, policy.id)
    reader = csv.DictReader(io.StringIO(csv_text))
    assert list(reader) == []

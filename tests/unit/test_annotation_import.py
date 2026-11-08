"""Tests for the annotation import adapter using SYNTHETIC fixture rows
only, shaped exactly like scripts/annotation/finalize.py's real output
schema. No real annotation data is used anywhere in this file -- these
are fabricated test rows, clearly labeled as such."""
from backend.app.models.comment import Comment
from backend.app.models.policy import PolicyDocument
from backend.app.models.stance import StancePrediction
from backend.app.services.annotation_import import import_finalized_annotations


def _policy(db_session):
    p = PolicyDocument(title="Synthetic Test Policy")
    db_session.add(p)
    db_session.commit()
    return p


def _finalized_row(**overrides) -> dict:
    """A synthetic row matching finalize.py's exact column schema."""
    row = {
        "comment_id": "PL-000001",
        "comment_text": "This is a synthetic fixture comment, not real annotation data.",
        "policy_context": "Synthetic context",
        "policy_section": "Synthetic section",
        "annotator_label": "Support",
        "exclusion_code": "",
        "annotation_confidence": "3",
        "annotation_notes": "",
        "source_unique_id": "1",
        "source_dataset": "synthetic_fixture",
        "language": "English",
        "word_count": "10",
    }
    row.update(overrides)
    return row


# ---- happy path ---------------------------------------------------------------

def test_import_creates_comment_and_prediction(db_session):
    policy = _policy(db_session)
    report = import_finalized_annotations(db_session, policy.id, [_finalized_row()], source_label="synthetic.csv")

    assert report.comments_created == 1
    assert report.predictions_created == 1
    assert report.error_count == 0

    comment = db_session.query(Comment).filter_by(policy_document_id=policy.id).one()
    assert comment.original_text == _finalized_row()["comment_text"]
    pred = db_session.query(StancePrediction).filter_by(comment_id=comment.id).one()
    assert pred.label.value == "Support"
    assert pred.source.value == "human"
    assert pred.confidence == 3


def test_exclusion_coded_row_creates_no_stance_label(db_session):
    policy = _policy(db_session)
    row = _finalized_row(annotator_label="", exclusion_code="SPAM")
    report = import_finalized_annotations(db_session, policy.id, [row], source_label="synthetic.csv")
    assert report.predictions_created == 1
    pred = db_session.query(StancePrediction).one()
    assert pred.label is None
    assert pred.exclusion_code.value == "SPAM"


# ---- independent re-validation: never trust "finalized" blindly ------------

def test_row_with_both_label_and_exclusion_is_rejected(db_session):
    policy = _policy(db_session)
    row = _finalized_row(annotator_label="Support", exclusion_code="SPAM")
    report = import_finalized_annotations(db_session, policy.id, [row], source_label="bad.csv")
    assert report.error_count == 1
    assert report.comments_created == 0


def test_pending_row_neither_label_nor_exclusion_is_rejected(db_session):
    """A row claiming to be 'finalized' but actually still pending must
    be caught, not silently imported as if it were a real decision."""
    policy = _policy(db_session)
    row = _finalized_row(annotator_label="", exclusion_code="")
    report = import_finalized_annotations(db_session, policy.id, [row], source_label="bad.csv")
    assert report.error_count == 1
    assert "not actually finalized" in report.errors[0].message


def test_invalid_label_value_is_rejected(db_session):
    policy = _policy(db_session)
    row = _finalized_row(annotator_label="Mixed")  # not one of the 4 finalized labels
    report = import_finalized_annotations(db_session, policy.id, [row], source_label="bad.csv")
    assert report.error_count == 1


def test_unclear_label_without_notes_still_imports(db_session):
    """This adapter imports whatever finalize.py already validated as
    complete -- it does not re-enforce every scripts/annotation/validate.py
    rule (e.g. Unclear-requires-notes), only structural correctness
    (valid label/exclusion values, mutual exclusivity, non-pending)."""
    policy = _policy(db_session)
    row = _finalized_row(annotator_label="Unclear", annotation_notes="")
    report = import_finalized_annotations(db_session, policy.id, [row], source_label="x.csv")
    assert report.predictions_created == 1


# ---- idempotency --------------------------------------------------------------

def test_reimporting_same_finalized_file_is_idempotent(db_session):
    policy = _policy(db_session)
    rows = [_finalized_row()]
    r1 = import_finalized_annotations(db_session, policy.id, rows, source_label="run1.csv")
    r2 = import_finalized_annotations(db_session, policy.id, rows, source_label="run2.csv")

    assert r1.comments_created == 1 and r1.predictions_created == 1
    assert r2.comments_created == 0 and r2.predictions_created == 0
    assert r2.comments_reused == 1
    assert r2.skipped_already_imported_count == 1

    assert db_session.query(Comment).count() == 1
    assert db_session.query(StancePrediction).count() == 1


def test_multiple_distinct_comments_import_correctly(db_session):
    policy = _policy(db_session)
    rows = [
        _finalized_row(comment_id="PL-000001", source_unique_id="1", annotator_label="Support"),
        _finalized_row(comment_id="PL-000002", source_unique_id="2", annotator_label="Oppose",
                        comment_text="A different synthetic comment."),
        _finalized_row(comment_id="PL-000003", source_unique_id="3", exclusion_code="OFF_TOPIC",
                        annotator_label="", comment_text="Off topic synthetic fixture."),
    ]
    report = import_finalized_annotations(db_session, policy.id, rows, source_label="batch.csv")
    assert report.comments_created == 3
    assert report.predictions_created == 3
    assert report.error_count == 0


def test_never_fabricates_a_label_for_a_row_that_lacks_one(db_session):
    """Sanity guard: if a row has no label/exclusion, the adapter must
    reject it (tested above) rather than ever inventing a default value
    like Neutral or an empty-string placeholder stance."""
    policy = _policy(db_session)
    row = _finalized_row(annotator_label="", exclusion_code="")
    import_finalized_annotations(db_session, policy.id, [row], source_label="x.csv")
    assert db_session.query(StancePrediction).count() == 0

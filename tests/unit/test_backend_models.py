import pytest
from sqlalchemy.exc import IntegrityError

from backend.app.models.comment import Comment, CommentSourceMetadata
from backend.app.models.concern import ConcernGroup, GroupMembership, RepresentativeComment
from backend.app.models.enums import ExclusionCode, ModelComponent, PredictionSource, StanceLabel, SummaryMethod
from backend.app.models.policy import PolicyDocument
from backend.app.models.stance import StancePrediction
from backend.app.models.summary import EvidenceReference, Summary
from backend.app.models.versioning import ModelVersion
from backend.app.services.validation import check_traceability_integrity, hash_normalized_text, normalize_text


def _make_policy(db_session):
    policy = PolicyDocument(title="Test Policy")
    db_session.add(policy)
    db_session.commit()
    return policy


def _make_comment(db_session, policy, text="A test comment about the policy."):
    normalized = normalize_text(text)
    comment = Comment(
        policy_document_id=policy.id,
        original_text=text,
        normalized_text=normalized,
        normalized_text_hash=hash_normalized_text(text),
        language="English",
    )
    db_session.add(comment)
    db_session.flush()
    db_session.add(
        CommentSourceMetadata(comment_id=comment.id, source_dataset="synthetic", source_record_id="1")
    )
    db_session.commit()
    return comment


# ---- database operations: basic CRUD + relationships -----------------------

def test_create_policy_and_comment(db_session):
    policy = _make_policy(db_session)
    comment = _make_comment(db_session, policy)
    assert comment.id is not None
    assert comment.source_metadata.source_dataset == "synthetic"


def test_comment_original_text_round_trips_unchanged(db_session):
    policy = _make_policy(db_session)
    text = "Exactly   this text,\nwith a newline and weird   spacing."
    comment = _make_comment(db_session, policy, text=text)
    db_session.refresh(comment)
    assert comment.original_text == text  # verbatim, not normalized


# ---- stance predictions: mutual exclusivity + source constraint -----------

def test_stance_label_alone_is_valid(db_session):
    policy = _make_policy(db_session)
    comment = _make_comment(db_session, policy)
    pred = StancePrediction(
        comment_id=comment.id, label=StanceLabel.SUPPORT, confidence=3,
        source=PredictionSource.HUMAN, annotator_or_model_ref="test-annotator",
    )
    db_session.add(pred)
    db_session.commit()
    assert pred.id is not None


def test_stance_label_and_exclusion_code_together_is_rejected(db_session):
    policy = _make_policy(db_session)
    comment = _make_comment(db_session, policy)
    pred = StancePrediction(
        comment_id=comment.id, label=StanceLabel.SUPPORT, exclusion_code=ExclusionCode.SPAM,
        source=PredictionSource.HUMAN, annotator_or_model_ref="test-annotator",
    )
    db_session.add(pred)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_model_source_without_model_version_is_rejected(db_session):
    policy = _make_policy(db_session)
    comment = _make_comment(db_session, policy)
    pred = StancePrediction(
        comment_id=comment.id, label=StanceLabel.OPPOSE,
        source=PredictionSource.MODEL, annotator_or_model_ref="clf-v1", model_version_id=None,
    )
    db_session.add(pred)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_model_source_with_model_version_is_valid(db_session):
    policy = _make_policy(db_session)
    comment = _make_comment(db_session, policy)
    version = ModelVersion(
        component=ModelComponent.STANCE_CLASSIFIER, name="tfidf-logreg", version_string="v1", config={}
    )
    db_session.add(version)
    db_session.flush()
    pred = StancePrediction(
        comment_id=comment.id, label=StanceLabel.OPPOSE,
        source=PredictionSource.MODEL, annotator_or_model_ref="clf-v1", model_version_id=version.id,
    )
    db_session.add(pred)
    db_session.commit()
    assert pred.id is not None


def test_repeat_pass_number_is_tracked_independently(db_session):
    policy = _make_policy(db_session)
    comment = _make_comment(db_session, policy)
    p1 = StancePrediction(
        comment_id=comment.id, label=StanceLabel.NEUTRAL, source=PredictionSource.HUMAN,
        annotator_or_model_ref="owner", pass_number=1,
    )
    p2 = StancePrediction(
        comment_id=comment.id, label=StanceLabel.NEUTRAL, source=PredictionSource.HUMAN,
        annotator_or_model_ref="owner", pass_number=2,
    )
    db_session.add_all([p1, p2])
    db_session.commit()
    assert {p.pass_number for p in comment.stance_predictions} == {1, 2}


# ---- concern grouping: independence from stance, noise handling ----------

def test_different_stances_can_share_a_concern_group(db_session):
    """The core independence principle: two comments with opposite
    stances can legitimately belong to the same concern group."""
    policy = _make_policy(db_session)
    c1 = _make_comment(db_session, policy, text="The fee increase is too high, I oppose it.")
    c2 = _make_comment(db_session, policy, text="The fee increase is reasonable, I support it.")

    version = ModelVersion(component=ModelComponent.CLUSTERING, name="hdbscan", version_string="v1", config={})
    db_session.add(version)
    db_session.flush()

    group = ConcernGroup(policy_document_id=policy.id, model_version_id=version.id, method="hdbscan", size=2)
    db_session.add(group)
    db_session.flush()

    db_session.add_all([
        GroupMembership(comment_id=c1.id, group_id=group.id, model_version_id=version.id),
        GroupMembership(comment_id=c2.id, group_id=group.id, model_version_id=version.id),
    ])
    db_session.add_all([
        StancePrediction(comment_id=c1.id, label=StanceLabel.OPPOSE, source=PredictionSource.HUMAN, annotator_or_model_ref="owner"),
        StancePrediction(comment_id=c2.id, label=StanceLabel.SUPPORT, source=PredictionSource.HUMAN, annotator_or_model_ref="owner"),
    ])
    db_session.commit()

    labels_in_group = {p.label for c in (c1, c2) for p in c.stance_predictions}
    assert labels_in_group == {StanceLabel.OPPOSE, StanceLabel.SUPPORT}


def test_noise_comments_are_not_force_assigned_but_still_tracked(db_session):
    policy = _make_policy(db_session)
    comment = _make_comment(db_session, policy)
    version = ModelVersion(component=ModelComponent.CLUSTERING, name="hdbscan", version_string="v1", config={})
    db_session.add(version)
    db_session.flush()

    noise_group = ConcernGroup(
        policy_document_id=policy.id, model_version_id=version.id, method="hdbscan", size=1, is_noise=True
    )
    db_session.add(noise_group)
    db_session.flush()
    db_session.add(GroupMembership(comment_id=comment.id, group_id=noise_group.id, model_version_id=version.id))
    db_session.commit()

    assert noise_group.is_noise is True
    assert len(noise_group.memberships) == 1  # still queryable, not dropped


def test_one_group_per_comment_per_clustering_run(db_session):
    policy = _make_policy(db_session)
    comment = _make_comment(db_session, policy)
    version = ModelVersion(component=ModelComponent.CLUSTERING, name="hdbscan", version_string="v1", config={})
    db_session.add(version)
    db_session.flush()
    g1 = ConcernGroup(policy_document_id=policy.id, model_version_id=version.id, method="hdbscan", size=1)
    g2 = ConcernGroup(policy_document_id=policy.id, model_version_id=version.id, method="hdbscan", size=1)
    db_session.add_all([g1, g2])
    db_session.flush()

    db_session.add(GroupMembership(comment_id=comment.id, group_id=g1.id, model_version_id=version.id))
    db_session.commit()

    db_session.add(GroupMembership(comment_id=comment.id, group_id=g2.id, model_version_id=version.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ---- evidence references / traceability ------------------------------------

def test_summary_with_evidence_passes_traceability_check(db_session):
    policy = _make_policy(db_session)
    comment = _make_comment(db_session, policy)
    version = ModelVersion(component=ModelComponent.CLUSTERING, name="hdbscan", version_string="v1", config={})
    db_session.add(version)
    db_session.flush()
    group = ConcernGroup(policy_document_id=policy.id, model_version_id=version.id, method="hdbscan", size=1)
    db_session.add(group)
    db_session.flush()
    db_session.add(RepresentativeComment(group_id=group.id, comment_id=comment.id, rank=1))
    summary = Summary(group_id=group.id, text=comment.original_text, method=SummaryMethod.EXTRACTIVE)
    db_session.add(summary)
    db_session.flush()
    db_session.add(EvidenceReference(summary_id=summary.id, comment_id=comment.id, rank=1))
    db_session.commit()

    assert check_traceability_integrity(db_session) == []


def test_summary_without_evidence_fails_traceability_check(db_session):
    policy = _make_policy(db_session)
    version = ModelVersion(component=ModelComponent.CLUSTERING, name="hdbscan", version_string="v1", config={})
    db_session.add(version)
    db_session.flush()
    group = ConcernGroup(policy_document_id=policy.id, model_version_id=version.id, method="hdbscan", size=0)
    db_session.add(group)
    db_session.flush()

    # A summary created with no EvidenceReference rows at all -- invalid per DATA_MODEL.md.
    summary = Summary(group_id=group.id, text="orphaned summary", method=SummaryMethod.EXTRACTIVE)
    db_session.add(summary)
    db_session.commit()

    problems = check_traceability_integrity(db_session)
    assert any("has zero evidence references" in p for p in problems)


def test_evidence_once_per_summary_constraint(db_session):
    policy = _make_policy(db_session)
    comment = _make_comment(db_session, policy)
    version = ModelVersion(component=ModelComponent.CLUSTERING, name="hdbscan", version_string="v1", config={})
    db_session.add(version)
    db_session.flush()
    group = ConcernGroup(policy_document_id=policy.id, model_version_id=version.id, method="hdbscan", size=1)
    db_session.add(group)
    db_session.flush()
    summary = Summary(group_id=group.id, text="x", method=SummaryMethod.EXTRACTIVE)
    db_session.add(summary)
    db_session.flush()
    db_session.add(EvidenceReference(summary_id=summary.id, comment_id=comment.id, rank=1))
    db_session.commit()

    db_session.add(EvidenceReference(summary_id=summary.id, comment_id=comment.id, rank=2))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

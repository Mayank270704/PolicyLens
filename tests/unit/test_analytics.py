from backend.app.models.comment import Comment, CommentSourceMetadata
from backend.app.models.concern import ConcernGroup
from backend.app.models.enums import ModelComponent, PredictionSource, StanceLabel
from backend.app.models.policy import PolicyDocument
from backend.app.models.stance import StancePrediction
from backend.app.models.versioning import ModelVersion
from backend.app.services.analytics import compute_cross_policy_summary, compute_policy_analytics
from backend.app.services.validation import hash_normalized_text, normalize_text


def _policy(db_session, title="P"):
    p = PolicyDocument(title=title)
    db_session.add(p)
    db_session.commit()
    return p


def _comment(db_session, policy, text, source_dataset="a", language="English"):
    normalized = normalize_text(text)
    c = Comment(
        policy_document_id=policy.id, original_text=text, normalized_text=normalized,
        normalized_text_hash=hash_normalized_text(text), language=language,
    )
    db_session.add(c)
    db_session.flush()
    db_session.add(CommentSourceMetadata(comment_id=c.id, source_dataset=source_dataset, source_record_id="1"))
    db_session.commit()
    return c


def test_total_comments_and_by_source(db_session):
    policy = _policy(db_session)
    _comment(db_session, policy, "a", source_dataset="dataset_x")
    _comment(db_session, policy, "b", source_dataset="dataset_x")
    _comment(db_session, policy, "c", source_dataset="dataset_y")

    result = compute_policy_analytics(db_session, policy.id)
    assert result.total_comments == 3
    assert result.comments_by_source == {"dataset_x": 2, "dataset_y": 1}


def test_language_distribution(db_session):
    policy = _policy(db_session)
    _comment(db_session, policy, "a", language="English")
    _comment(db_session, policy, "b", language="English")
    _comment(db_session, policy, "c", language="French")

    result = compute_policy_analytics(db_session, policy.id)
    assert result.language_distribution == {"English": 2, "French": 1}


def test_submission_timeline_buckets_by_date(db_session):
    policy = _policy(db_session)
    _comment(db_session, policy, "a")
    result = compute_policy_analytics(db_session, policy.id)
    assert sum(result.submission_timeline.values()) == 1


def test_data_quality_counts_duplicates_and_validation_status(db_session):
    policy = _policy(db_session)
    c1 = _comment(db_session, policy, "same text", source_dataset="x")
    c1.multiplicity = 3
    c1.validation_status = "validated"
    c2 = _comment(db_session, policy, "other text")
    c2.pii_flagged = True
    db_session.commit()

    result = compute_policy_analytics(db_session, policy.id)
    assert result.data_quality["duplicate_text_merge_count"] == 1
    assert result.data_quality["max_multiplicity"] == 3
    assert result.data_quality["pii_flagged_count"] == 1
    assert result.data_quality["validated_count"] == 1


# ---- the core "unavailable vs zero" distinction -----------------------------

def test_stance_unavailable_when_no_predictions_exist_at_all(db_session):
    policy = _policy(db_session)
    _comment(db_session, policy, "a comment with no stance yet")
    result = compute_policy_analytics(db_session, policy.id)
    assert result.stance_available is False
    assert result.stance_distribution == {}
    assert result.pending_stance_count == 1


def test_stance_available_true_once_at_least_one_prediction_exists(db_session):
    policy = _policy(db_session)
    c = _comment(db_session, policy, "a comment with a stance")
    db_session.add(StancePrediction(
        comment_id=c.id, label=StanceLabel.SUPPORT, source=PredictionSource.HUMAN, annotator_or_model_ref="owner",
    ))
    db_session.commit()

    result = compute_policy_analytics(db_session, policy.id)
    assert result.stance_available is True
    assert result.stance_distribution == {"Support": 1}
    assert result.pending_stance_count == 0


def test_concern_groups_unavailable_before_any_clustering_run(db_session):
    policy = _policy(db_session)
    _comment(db_session, policy, "a")
    result = compute_policy_analytics(db_session, policy.id)
    assert result.concern_groups_available is False
    assert result.concern_group_count == 0


def test_concern_groups_available_and_noise_counted_separately(db_session):
    policy = _policy(db_session)
    version = ModelVersion(component=ModelComponent.CLUSTERING, name="hdbscan", version_string="v1", config={})
    db_session.add(version)
    db_session.flush()
    db_session.add(ConcernGroup(policy_document_id=policy.id, model_version_id=version.id, method="hdbscan", size=5))
    db_session.add(ConcernGroup(
        policy_document_id=policy.id, model_version_id=version.id, method="hdbscan", size=2, is_noise=True
    ))
    db_session.commit()

    result = compute_policy_analytics(db_session, policy.id)
    assert result.concern_groups_available is True
    assert result.concern_group_count == 1  # noise group excluded from the "real concern group" count
    assert result.noise_comment_count == 2


# ---- cross-policy summary ----------------------------------------------------

def test_cross_policy_summary(db_session):
    p1 = _policy(db_session, "Policy A")
    p2 = _policy(db_session, "Policy B")
    _comment(db_session, p1, "a")
    _comment(db_session, p1, "b")
    _comment(db_session, p2, "c")

    result = compute_cross_policy_summary(db_session)
    assert result.total_comments == 3
    assert result.comments_by_policy == {"Policy A": 2, "Policy B": 1}
    assert result.total_policies == 2


def test_cross_policy_summary_includes_policies_with_zero_comments(db_session):
    _policy(db_session, "Empty Policy")
    result = compute_cross_policy_summary(db_session)
    assert result.comments_by_policy == {"Empty Policy": 0}

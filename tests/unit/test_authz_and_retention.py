from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from backend.app.models.comment import Comment
from backend.app.models.policy import PolicyDocument
from backend.app.services.authz import CurrentUser, Role, get_current_user, require_role
from backend.app.services.retention import find_retention_candidates
from backend.app.services.validation import hash_normalized_text, normalize_text


# ---- role-based authorization interface -------------------------------------

def test_default_current_user_is_admin():
    user = get_current_user()
    assert user.role == Role.ADMIN


def test_require_role_allows_sufficient_role():
    dependency = require_role(Role.RESEARCHER)
    result = dependency(current_user=CurrentUser(user_id="u1", role=Role.ADMIN))
    assert result.role == Role.ADMIN


def test_require_role_allows_exact_match():
    dependency = require_role(Role.RESEARCHER)
    result = dependency(current_user=CurrentUser(user_id="u1", role=Role.RESEARCHER))
    assert result.role == Role.RESEARCHER


def test_require_role_rejects_insufficient_role():
    dependency = require_role(Role.ADMIN)
    with pytest.raises(HTTPException) as exc_info:
        dependency(current_user=CurrentUser(user_id="u1", role=Role.PUBLIC))
    assert exc_info.value.status_code == 403


def test_require_role_rejects_public_from_researcher_gate():
    dependency = require_role(Role.RESEARCHER)
    with pytest.raises(HTTPException):
        dependency(current_user=CurrentUser(user_id="u1", role=Role.PUBLIC))


# ---- data retention: identifies candidates, never deletes -------------------

def _old_comment(db_session, policy, days_old):
    text = f"comment {days_old} days old"
    c = Comment(
        policy_document_id=policy.id, original_text=text, normalized_text=normalize_text(text),
        normalized_text_hash=hash_normalized_text(text), language="English",
    )
    db_session.add(c)
    db_session.commit()
    c.created_at = datetime.now(timezone.utc) - timedelta(days=days_old)
    db_session.commit()
    return c


def test_no_retention_policy_configured_returns_empty(db_session, monkeypatch):
    from backend.app import config as config_module
    monkeypatch.delenv("RETENTION_POLICY_DAYS", raising=False)

    policy = PolicyDocument(title="P")
    db_session.add(policy)
    db_session.commit()
    _old_comment(db_session, policy, days_old=10000)

    candidates = find_retention_candidates(db_session, policy.id)
    assert candidates == []  # indefinite retention is the default; nothing is ever a "candidate"


def test_retention_candidates_identified_but_not_deleted(db_session, monkeypatch):
    monkeypatch.setenv("RETENTION_POLICY_DAYS", "30")

    policy = PolicyDocument(title="P")
    db_session.add(policy)
    db_session.commit()
    old_comment = _old_comment(db_session, policy, days_old=100)
    recent_comment = _old_comment(db_session, policy, days_old=1)

    candidates = find_retention_candidates(db_session, policy.id)
    candidate_ids = {c.id for c in candidates}
    assert old_comment.id in candidate_ids
    assert recent_comment.id not in candidate_ids

    # Nothing was deleted -- both rows still exist in the database.
    assert db_session.get(Comment, old_comment.id) is not None
    assert db_session.get(Comment, recent_comment.id) is not None

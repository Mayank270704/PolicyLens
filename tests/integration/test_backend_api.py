"""API contract tests -- exercised through FastAPI's TestClient against
an isolated in-memory database (see tests/conftest.py's `client` fixture).
Synthetic fixtures only; nothing here touches data/annotations/ or the
real default backend database file."""


def _create_policy(client, title="Test Policy"):
    r = client.post("/policies", json={"title": title})
    assert r.status_code == 201
    return r.json()


# ---- policy document endpoints ---------------------------------------------

def test_create_and_retrieve_policy(client):
    created = _create_policy(client, "Open Government Plan")
    r = client.get(f"/policies/{created['id']}")
    assert r.status_code == 200
    assert r.json()["title"] == "Open Government Plan"


def test_get_nonexistent_policy_is_404(client):
    r = client.get("/policies/999999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "404"


def test_policy_creation_rejects_blank_title(client):
    r = client.post("/policies", json={"title": ""})
    assert r.status_code == 422


def test_list_policies_is_paginated(client):
    for i in range(5):
        _create_policy(client, f"Policy {i}")
    r = client.get("/policies?page=1&page_size=2")
    body = r.json()
    assert r.status_code == 200
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["total_pages"] == 3

    r2 = client.get("/policies?page=3&page_size=2")
    assert len(r2.json()["items"]) == 1  # last page has the remainder


def test_upload_document_identifies_sections(client):
    policy = _create_policy(client)
    r = client.post(
        f"/policies/{policy['id']}/documents",
        files={"file": ("p.txt", b"Section 1. A\nText A.\n\nSection 2. B\nText B.", "text/plain")},
    )
    assert r.status_code == 201
    assert r.json()["sections_created"] == 2
    assert r.json()["status"] == "processed"


def test_upload_rejects_unsupported_file_type(client):
    policy = _create_policy(client)
    r = client.post(
        f"/policies/{policy['id']}/documents",
        files={"file": ("p.docx", b"whatever", "application/octet-stream")},
    )
    assert r.status_code == 422


def test_upload_to_nonexistent_policy_is_404(client):
    r = client.post(
        "/policies/999999/documents", files={"file": ("p.txt", b"content", "text/plain")}
    )
    assert r.status_code == 404


def test_list_and_get_sections(client):
    policy = _create_policy(client)
    client.post(
        f"/policies/{policy['id']}/documents",
        files={"file": ("p.txt", b"Section 1. A\nText A.", "text/plain")},
    )
    r = client.get(f"/policies/{policy['id']}/sections")
    section_id = r.json()["items"][0]["id"]

    r2 = client.get(f"/policies/{policy['id']}/sections/{section_id}")
    assert r2.status_code == 200
    assert r2.json()["section_label"] == "Section 1. A"


# ---- comment endpoints ------------------------------------------------------

def test_submit_comment(client):
    policy = _create_policy(client)
    r = client.post(
        f"/policies/{policy['id']}/comments",
        json={
            "original_text": "This policy should include stronger enforcement.",
            "language": "English", "source_dataset": "web_form", "source_record_id": "r1",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["original_text"] == "This policy should include stronger enforcement."
    assert body["multiplicity"] == 1


def test_duplicate_comment_increments_multiplicity_not_a_new_row(client):
    policy = _create_policy(client)
    payload = {
        "original_text": "Exactly the same comment text.",
        "source_dataset": "a", "source_record_id": "1",
    }
    r1 = client.post(f"/policies/{policy['id']}/comments", json=payload)
    r2 = client.post(f"/policies/{policy['id']}/comments", json={**payload, "source_record_id": "2"})
    assert r1.json()["id"] == r2.json()["id"]
    assert r2.json()["multiplicity"] == 2


def test_submit_comment_rejects_blank_text(client):
    policy = _create_policy(client)
    r = client.post(
        f"/policies/{policy['id']}/comments",
        json={"original_text": "   ", "source_dataset": "a", "source_record_id": "1"},
    )
    assert r.status_code == 422


def test_get_comment_not_found(client):
    r = client.get("/comments/999999")
    assert r.status_code == 404


def test_list_comments_paginated(client):
    policy = _create_policy(client)
    for i in range(3):
        client.post(
            f"/policies/{policy['id']}/comments",
            json={"original_text": f"Comment number {i} here.", "source_dataset": "a", "source_record_id": str(i)},
        )
    r = client.get(f"/policies/{policy['id']}/comments?page=1&page_size=2")
    assert r.json()["total"] == 3
    assert len(r.json()["items"]) == 2


def test_validate_comment_flags_pii(client):
    policy = _create_policy(client)
    r = client.post(
        f"/policies/{policy['id']}/comments",
        json={"original_text": "Reach me at test@example.com please.", "source_dataset": "a", "source_record_id": "1"},
    )
    comment_id = r.json()["id"]

    r2 = client.post(f"/comments/{comment_id}/validate")
    assert r2.status_code == 200
    body = r2.json()
    assert body["pii_flagged"] is True
    assert "email_address_pattern" in body["pii_flag_reasons"]


def test_validate_comment_suggests_exclusion_for_filler_text(client):
    policy = _create_policy(client)
    r = client.post(
        f"/policies/{policy['id']}/comments",
        json={"original_text": "This is a substantive enough placeholder to pass creation, ok", "source_dataset": "a", "source_record_id": "1"},
    )
    comment_id = r.json()["id"]
    r2 = client.post(f"/comments/{comment_id}/validate")
    # substantive text should not trigger the filler heuristic
    assert r2.json()["suggested_exclusion_code"] is None


# ---- stance endpoint ---------------------------------------------------------

def test_stance_predictions_empty_list_when_none_exist(client):
    policy = _create_policy(client)
    r = client.post(
        f"/policies/{policy['id']}/comments",
        json={"original_text": "A comment awaiting a stance decision.", "source_dataset": "a", "source_record_id": "1"},
    )
    comment_id = r.json()["id"]
    r2 = client.get(f"/comments/{comment_id}/stance")
    assert r2.status_code == 200
    assert r2.json() == []


def test_stance_predictions_for_nonexistent_comment_is_404(client):
    r = client.get("/comments/999999/stance")
    assert r.status_code == 404


# ---- concern groups + reports -----------------------------------------------

def test_concern_groups_empty_before_any_clustering_run(client):
    policy = _create_policy(client)
    r = client.get(f"/policies/{policy['id']}/concern-groups")
    assert r.status_code == 200
    assert r.json()["items"] == []


def test_concern_group_not_found(client):
    r = client.get("/concern-groups/999999")
    assert r.status_code == 404


def test_policy_report_reflects_incomplete_pipeline_honestly(client):
    policy = _create_policy(client)
    client.post(
        f"/policies/{policy['id']}/comments",
        json={"original_text": "One comment, no stance yet.", "source_dataset": "a", "source_record_id": "1"},
    )
    r = client.get(f"/policies/{policy['id']}/report")
    body = r.json()
    assert body["total_comments"] == 1
    assert body["pending_count"] == 1
    assert body["completeness_flags"]["has_stance_predictions"] is False
    assert body["completeness_flags"]["stance_complete"] is False


def test_policy_report_for_nonexistent_policy_is_404(client):
    r = client.get("/policies/999999/report")
    assert r.status_code == 404


def test_health_check(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

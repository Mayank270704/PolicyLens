"""Phase 7 -- full synthetic workflow, exercised through the real HTTP
API (tests/conftest.py's `client` fixture, isolated in-memory database).
All data here is synthetic/fabricated test input; nothing touches
data/annotations/ or any real submission."""
import csv
import io


def test_complete_workflow_create_to_analytics(client):
    # 1. Create a policy
    r = client.post("/policies", json={
        "title": "Synthetic Open Data Policy", "description": "A fixture policy for workflow testing.",
    })
    assert r.status_code == 201
    policy_id = r.json()["id"]

    # 2. Upload a policy document
    doc_text = (
        b"Section 1. Transparency\n"
        b"The government commits to publishing all operational data openly.\n\n"
        b"Section 2. Accountability\n"
        b"An independent oversight body will review compliance annually."
    )
    r = client.post(f"/policies/{policy_id}/documents", files={"file": ("policy.txt", doc_text, "text/plain")})
    assert r.status_code == 201
    assert r.json()["sections_created"] == 2

    # 3. Extract and retrieve sections
    r = client.get(f"/policies/{policy_id}/sections")
    sections = r.json()["items"]
    assert len(sections) == 2
    transparency_section = next(s for s in sections if "Transparency" in s["section_label"])

    r = client.get(f"/policies/{policy_id}/retrieve", params={"query": "transparency open data"})
    assert r.status_code == 200
    retrieval_results = r.json()["results"]
    assert len(retrieval_results) >= 1
    assert retrieval_results[0]["section_id"] == transparency_section["id"]
    assert "accuracy" not in r.json()  # no bare accuracy claim field anywhere in the response
    assert "No retrieval accuracy" in r.json()["accuracy_disclaimer"]

    # 4. Import public comments (bulk CSV)
    csv_buf = io.StringIO()
    writer = csv.DictWriter(csv_buf, fieldnames=["original_text", "source_dataset", "source_record_id", "language"])
    writer.writeheader()
    comment_texts = [
        "I strongly support increased transparency in government data.",
        "The accountability measures seem reasonable to me.",
        "This policy does not go far enough on enforcement.",
        "What is the timeline for implementation?",
        "spam spam buy cheap watches now",
    ]
    for i, text in enumerate(comment_texts):
        writer.writerow({
            "original_text": text, "source_dataset": "synthetic_workflow_test",
            "source_record_id": str(i), "language": "English",
        })
    csv_bytes = csv_buf.getvalue().encode("utf-8")

    r = client.post(
        f"/policies/{policy_id}/comments/bulk-import",
        files={"file": ("comments.csv", csv_bytes, "text/csv")},
    )
    assert r.status_code == 201
    import_report = r.json()
    assert import_report["created_count"] == 5
    assert import_report["error_count"] == 0

    # 5. Validate comments (PII / exclusion heuristic)
    r = client.get(f"/policies/{policy_id}/comments", params={"page_size": 50})
    comments = r.json()["items"]
    assert len(comments) == 5
    spam_comment = next(c for c in comments if "spam" in c["original_text"].lower())
    r = client.post(f"/comments/{spam_comment['id']}/validate")
    assert r.status_code == 200
    # the spam heuristic is intentionally narrow (see services/validation.py) --
    # it won't necessarily flag this, so we only assert the endpoint ran cleanly
    # and returned a real structural result, not that it caught this specific case.
    assert "validation_status" in r.json()

    # 6. Retrieve comments (already exercised above; re-check pagination + single-get)
    r = client.get(f"/comments/{comments[0]['id']}")
    assert r.status_code == 200
    assert r.json()["original_text"] == comments[0]["original_text"]

    # 7. Run available non-ML analytics
    r = client.get(f"/policies/{policy_id}/analytics")
    assert r.status_code == 200
    analytics = r.json()
    assert analytics["total_comments"] == 5
    assert analytics["comments_by_source"] == {"synthetic_workflow_test": 5}
    assert analytics["language_distribution"] == {"English": 5}
    assert analytics["stance_available"] is False  # no ML has run -- correctly distinguished from "zero stance"
    assert analytics["concern_groups_available"] is False

    r = client.get(f"/policies/{policy_id}/report")
    assert r.status_code == 200
    report = r.json()
    assert report["total_comments"] == 5
    assert report["pending_count"] == 5
    assert report["completeness_flags"]["has_stance_predictions"] is False

    r = client.get("/analytics/summary")
    assert r.status_code == 200
    assert r.json()["comments_by_policy"]["Synthetic Open Data Policy"] == 5

    # 8. Verify evidence and provenance structures (export + import audit log)
    r = client.get(f"/policies/{policy_id}/comments/export")
    assert r.status_code == 200
    exported_rows = list(csv.DictReader(io.StringIO(r.text)))
    assert len(exported_rows) == 5
    assert set(row["original_text"] for row in exported_rows) == set(comment_texts)

    r = client.get(f"/policies/{policy_id}/import-runs")
    assert r.status_code == 200
    runs = r.json()["items"]
    assert len(runs) == 1
    assert runs[0]["import_type"] == "comment_csv"
    assert runs[0]["created_count"] == 5
    assert runs[0]["completed_at"] is not None


def test_annotation_import_workflow_end_to_end(client):
    """A second, independent workflow: create a policy, then import a
    SYNTHETIC finalized-annotation-shaped CSV (never real annotation
    data) and confirm it surfaces correctly through analytics/report."""
    r = client.post("/policies", json={"title": "Annotation Import Test Policy"})
    policy_id = r.json()["id"]

    buf = io.StringIO()
    fieldnames = [
        "comment_id", "comment_text", "policy_context", "policy_section",
        "annotator_label", "exclusion_code", "annotation_confidence", "annotation_notes",
        "source_unique_id", "source_dataset", "language", "word_count",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow({
        "comment_id": "PL-000001", "comment_text": "Synthetic fixture: I support this.",
        "policy_context": "ctx", "policy_section": "sec", "annotator_label": "Support",
        "exclusion_code": "", "annotation_confidence": "3", "annotation_notes": "",
        "source_unique_id": "1", "source_dataset": "synthetic_annotation_fixture",
        "language": "English", "word_count": "6",
    })
    writer.writerow({
        "comment_id": "PL-000002", "comment_text": "Synthetic fixture: unrelated spam text.",
        "policy_context": "ctx", "policy_section": "sec", "annotator_label": "",
        "exclusion_code": "SPAM", "annotation_confidence": "", "annotation_notes": "",
        "source_unique_id": "2", "source_dataset": "synthetic_annotation_fixture",
        "language": "English", "word_count": "5",
    })

    r = client.post(
        f"/policies/{policy_id}/annotations/import",
        files={"file": ("finalized_fixture.csv", buf.getvalue().encode("utf-8"), "text/csv")},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["comments_created"] == 2
    assert body["predictions_created"] == 2
    assert body["error_count"] == 0

    r = client.get(f"/policies/{policy_id}/analytics")
    analytics = r.json()
    assert analytics["stance_available"] is True
    assert analytics["stance_distribution"] == {"Support": 1}
    assert analytics["exclusion_distribution"] == {"SPAM": 1}

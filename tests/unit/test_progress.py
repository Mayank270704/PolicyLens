from scripts.annotation import progress, schema
from tests.unit.test_validate import make_row


def test_empty_batch_counts_are_zero():
    report = progress.build_report([])
    assert report["total_comments"] == 0
    assert report["completion_percentage"] == 0.0


def test_counts_pending_annotated_excluded_separately():
    rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", exclusion_code="SPAM"),
        make_row(comment_id="PL-3"),  # pending
    ]
    report = progress.build_report(rows)
    assert report["total_comments"] == 3
    assert report["annotated_comments"] == 1
    assert report["excluded_comments"] == 1
    assert report["pending_comments"] == 1


def test_pending_is_not_counted_as_excluded_or_annotated():
    rows = [make_row(comment_id="PL-1")]
    report = progress.build_report(rows)
    assert report["pending_comments"] == 1
    assert report["annotated_comments"] == 0
    assert report["excluded_comments"] == 0


def test_stance_distribution_counts_each_label():
    rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", annotator_label="Support", annotation_confidence="2"),
        make_row(comment_id="PL-3", annotator_label="Oppose", annotation_confidence="1"),
    ]
    report = progress.build_report(rows)
    assert report["stance_distribution"] == {"Oppose": 1, "Support": 2}


def test_excluded_by_reason_breakdown():
    rows = [
        make_row(comment_id="PL-1", exclusion_code="SPAM"),
        make_row(comment_id="PL-2", exclusion_code="SPAM"),
        make_row(comment_id="PL-3", exclusion_code="OFF_TOPIC"),
    ]
    report = progress.build_report(rows)
    assert report["excluded_by_reason"] == {"OFF_TOPIC": 1, "SPAM": 2}


def test_confidence_distribution_uses_readable_labels():
    rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", annotator_label="Neutral", annotation_confidence="3"),
        make_row(comment_id="PL-3", annotator_label="Oppose", annotation_confidence="1"),
    ]
    report = progress.build_report(rows)
    assert report["confidence_distribution"] == {"High": 2, "Low": 1}


def test_completion_percentage_counts_labeled_and_excluded():
    rows = [
        make_row(comment_id="PL-1", annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", exclusion_code="SPAM"),
        make_row(comment_id="PL-3"),
        make_row(comment_id="PL-4"),
    ]
    report = progress.build_report(rows)
    assert report["completion_percentage"] == 50.0


def test_completion_by_stratum_uses_source_dataset_and_length_bucket():
    rows = [
        make_row(comment_id="PL-1", source_dataset="dsA", word_count="3",
                 annotator_label="Support", annotation_confidence="3"),
        make_row(comment_id="PL-2", source_dataset="dsA", word_count="3"),  # same stratum, pending
        make_row(comment_id="PL-3", source_dataset="dsB", word_count="50", exclusion_code="SPAM"),
    ]
    report = progress.build_report(rows)
    key_a = f"dsA|{schema.length_bucket(3)}"
    key_b = f"dsB|{schema.length_bucket(50)}"
    assert report["completion_by_stratum"][key_a] == {"done": 1, "total": 2, "pct": 50.0}
    assert report["completion_by_stratum"][key_b] == {"done": 1, "total": 1, "pct": 100.0}
    assert report["n_strata"] == 2


def test_length_bucket_boundaries():
    assert schema.length_bucket(1) == "short"
    assert schema.length_bucket(schema.LENGTH_SHORT_MAX_WORDS) == "short"
    assert schema.length_bucket(schema.LENGTH_SHORT_MAX_WORDS + 1) == "medium"
    assert schema.length_bucket(schema.LENGTH_MEDIUM_MAX_WORDS) == "medium"
    assert schema.length_bucket(schema.LENGTH_MEDIUM_MAX_WORDS + 1) == "long"

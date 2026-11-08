from scripts.annotation import schema, validate

FIELDNAMES = list(schema.REQUIRED_COLUMNS)


def make_row(**overrides):
    row = {
        "comment_id": "PL-000001",
        "comment_text": "Sample comment text here.",
        "policy_context": "ctx",
        "policy_section": "sec",
        "annotator_label": "",
        "exclusion_code": "",
        "annotation_confidence": "",
        "annotation_notes": "",
        "source_unique_id": "1",
        "source_dataset": "get_involved_questionnaire_2017_18",
        "language": "English",
        "word_count": "5",
    }
    row.update(overrides)
    return row


def errors_of(issues, code=None):
    return [i for i in issues if i.severity == "ERROR" and (code is None or i.code == code)]


def warnings_of(issues, code=None):
    return [i for i in issues if i.severity == "WARNING" and (code is None or i.code == code)]


# ---- valid labels -----------------------------------------------------

def test_valid_stance_label_passes():
    rows = [make_row(annotator_label="Support", annotation_confidence="3")]
    issues = validate.validate_batch(rows)
    assert errors_of(issues) == []


def test_all_four_stance_labels_are_valid():
    for label in schema.STANCE_LABELS:
        rows = [make_row(annotator_label=label, annotation_confidence="2", annotation_notes="note")]
        issues = validate.validate_batch(rows)
        assert errors_of(issues, "INVALID_LABEL") == [], f"{label} should be valid"


# ---- invalid labels -----------------------------------------------------

def test_invalid_stance_label_is_rejected():
    rows = [make_row(annotator_label="Mixed")]
    issues = validate.validate_batch(rows)
    assert len(errors_of(issues, "INVALID_LABEL")) == 1


def test_invalid_exclusion_code_is_rejected():
    rows = [make_row(exclusion_code="NOT_A_REAL_CODE")]
    issues = validate.validate_batch(rows)
    assert len(errors_of(issues, "INVALID_EXCLUSION_CODE")) == 1


def test_all_exclusion_codes_are_valid():
    for code in schema.EXCLUSION_CODES:
        rows = [make_row(exclusion_code=code)]
        issues = validate.validate_batch(rows)
        assert errors_of(issues, "INVALID_EXCLUSION_CODE") == []


# ---- exclusion handling / mutual exclusivity ---------------------------

def test_excluded_comment_cannot_also_have_a_stance_label():
    rows = [make_row(annotator_label="Support", exclusion_code="SPAM")]
    issues = validate.validate_batch(rows)
    assert len(errors_of(issues, "LABEL_AND_EXCLUSION_SET")) == 1


def test_exclusion_alone_is_valid():
    rows = [make_row(exclusion_code="OFF_TOPIC")]
    issues = validate.validate_batch(rows)
    assert errors_of(issues) == []


# ---- pending vs required completeness ----------------------------------

def test_blank_row_is_fine_when_completeness_not_required():
    rows = [make_row()]
    issues = validate.validate_batch(rows, require_complete=False)
    assert errors_of(issues, "INCOMPLETE") == []


def test_blank_row_is_an_error_when_completeness_required():
    rows = [make_row()]
    issues = validate.validate_batch(rows, require_complete=True)
    assert len(errors_of(issues, "INCOMPLETE")) == 1


def test_labeled_row_is_not_incomplete():
    rows = [make_row(annotator_label="Neutral", annotation_confidence="3")]
    issues = validate.validate_batch(rows, require_complete=True)
    assert errors_of(issues, "INCOMPLETE") == []


def test_excluded_row_is_not_incomplete():
    rows = [make_row(exclusion_code="SPAM")]
    issues = validate.validate_batch(rows, require_complete=True)
    assert errors_of(issues, "INCOMPLETE") == []


# ---- confidence scale ---------------------------------------------------

def test_invalid_confidence_value_is_rejected():
    rows = [make_row(annotator_label="Support", annotation_confidence="5")]
    issues = validate.validate_batch(rows)
    assert len(errors_of(issues, "INVALID_CONFIDENCE")) == 1


def test_valid_confidence_values_pass():
    for v in schema.CONFIDENCE_VALUES:
        rows = [make_row(annotator_label="Support", annotation_confidence=v)]
        issues = validate.validate_batch(rows)
        assert errors_of(issues, "INVALID_CONFIDENCE") == []


def test_missing_confidence_on_labeled_row_warns_not_errors():
    rows = [make_row(annotator_label="Support", annotation_confidence="")]
    issues = validate.validate_batch(rows)
    assert errors_of(issues) == []
    assert len(warnings_of(issues, "MISSING_CONFIDENCE")) == 1


# ---- notes requirement for Unclear --------------------------------------

def test_unclear_without_notes_is_an_error():
    rows = [make_row(annotator_label="Unclear", annotation_confidence="2", annotation_notes="")]
    issues = validate.validate_batch(rows)
    assert len(errors_of(issues, "MISSING_REQUIRED_NOTES")) == 1


def test_unclear_with_notes_is_fine():
    rows = [make_row(annotator_label="Unclear", annotation_confidence="2", annotation_notes="Balanced, D5.")]
    issues = validate.validate_batch(rows)
    assert errors_of(issues) == []


# ---- duplicate / missing IDs --------------------------------------------

def test_duplicate_comment_ids_are_rejected():
    rows = [make_row(comment_id="PL-000001"), make_row(comment_id="PL-000001")]
    issues = validate.validate_batch(rows)
    assert len(errors_of(issues, "DUPLICATE_ID")) == 1


def test_missing_comment_id_is_rejected():
    rows = [make_row(comment_id="")]
    issues = validate.validate_batch(rows)
    assert len(errors_of(issues, "MISSING_ID")) == 1


def test_unique_ids_pass():
    rows = [make_row(comment_id=f"PL-{i:06d}") for i in range(5)]
    issues = validate.validate_batch(rows)
    assert errors_of(issues, "DUPLICATE_ID") == []


# ---- schema / column checks ---------------------------------------------

def test_missing_required_columns_detected():
    issues = validate.validate_schema_columns(["comment_id", "comment_text"])
    assert len(issues) == 1
    assert issues[0].code == "MISSING_COLUMNS"


def test_complete_columns_pass():
    issues = validate.validate_schema_columns(FIELDNAMES)
    assert issues == []


def test_non_integer_word_count_is_rejected():
    rows = [make_row(word_count="five")]
    issues = validate.validate_batch(rows)
    assert len(errors_of(issues, "INVALID_WORD_COUNT")) == 1


# ---- immutability of comment text / metadata ----------------------------

def test_unchanged_text_and_metadata_passes_immutability_check():
    backup = [make_row()]
    working = [make_row(annotator_label="Support", annotation_confidence="3")]
    issues = validate.validate_batch(working, backup_rows=backup)
    assert errors_of(issues, "IMMUTABLE_FIELD_CHANGED") == []


def test_changed_comment_text_is_detected():
    backup = [make_row()]
    working = [make_row(comment_text="This text was edited after generation.")]
    issues = validate.validate_batch(working, backup_rows=backup)
    assert len(errors_of(issues, "IMMUTABLE_FIELD_CHANGED")) == 1


def test_changed_source_metadata_is_detected():
    backup = [make_row()]
    working = [make_row(source_dataset="a_different_dataset")]
    issues = validate.validate_batch(working, backup_rows=backup)
    assert len(errors_of(issues, "IMMUTABLE_FIELD_CHANGED")) == 1


def test_row_missing_from_working_file_is_detected():
    backup = [make_row(comment_id="PL-000001"), make_row(comment_id="PL-000002")]
    working = [make_row(comment_id="PL-000001")]
    issues = validate.validate_batch(working, backup_rows=backup)
    assert len(errors_of(issues, "ID_MISSING_FROM_BATCH")) == 1


def test_row_inserted_not_in_backup_is_detected():
    backup = [make_row(comment_id="PL-000001")]
    working = [make_row(comment_id="PL-000001"), make_row(comment_id="PL-999999")]
    issues = validate.validate_batch(working, backup_rows=backup)
    assert len(errors_of(issues, "ID_NOT_IN_BACKUP")) == 1

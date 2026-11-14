"""Annotation schema for PROPOSED Indian stance codebook v2 (NOT ADOPTED).

Single source of truth for allowed values, used by the batch builders, the validator and the
training loader. Changing a value here is a methodology change and must be logged in
docs/annotation/ANNOTATION_CHANGELOG.md.
"""
from __future__ import annotations

SCHEMA_VERSION = "indian_stance_annotation_schema_v2_PROPOSED"
STANCE_LABELS = ("Support", "Oppose", "Neutral", "Unclear")
UNCLEAR_REASONS = ("MIXED", "AMBIGUOUS_TARGET", "CONDITIONAL_UNRESOLVED", "MISSING_CONTEXT", "TRUNCATED",
                   "SARCASM_UNRESOLVED")
EXCLUSION_CODES = ("OFF_TOPIC", "NON_SUBSTANTIVE", "ATTACHMENT_ONLY", "UNREADABLE", "WITHHELD_PRIVACY")
CONFIDENCE_VALUES = ("1", "2", "3")  # 1 low / borderline, 2 medium, 3 high: a property of the label
NEEDS_REVIEW_VALUES = ("yes", "no")  # a workflow request, recorded separately from confidence
NEEDS_REVIEW_REASONS = ("BORDERLINE", "LANGUAGE", "PRIVACY", "GUIDELINE_GAP", "OTHER")
RATIONALE_REQUIRED_FOR_STANCE = ("Oppose", "Unclear")
SENTIMENT_LIKE_VALUES = frozenset({"positive", "negative", "pos", "neg", "mixed", "0", "2", "4", "-1", "1"})

MYGOV_STANCE_TARGET = "GODL_INDIA_DRAFT_2016"  # draft Government Open Data Use License - India

LABEL_FIELDS_COMMON = ["exclusion_code", "stance", "unclear_reason", "confidence", "needs_review",
                       "needs_review_reason", "rationale", "annotator_id"]
MYGOV_SECONDARY_FIELDS = ["clause_referenced", "concern_type", "requested_action"]
TWEET_SECONDARY_FIELDS = ["stance_target", "sarcasm_or_irony"]

MYGOV_ITEM_FIELDS = ["item_id", "source", "batch_version", "annotation_order", "legacy_annotation_batch",
                     "representative_comment_id", "member_comment_ids", "group_size", "possible_truncation",
                     "has_attachment", "script_detected", "pii_handling", "clause_numbers_detected",
                     "normalised_text_sha256", "text_status", "stance_target"]
TWEET_ITEM_FIELDS = ["item_id", "source", "batch_version", "annotation_order", "tweet_row_id", "author_pseudo_id",
                     "month", "study_split", "annotation_batch", "plan_v2_status", "masked_text_group",
                     "script_detected", "text_status"]

MYGOV_BATCH_FIELDS = MYGOV_ITEM_FIELDS + LABEL_FIELDS_COMMON + MYGOV_SECONDARY_FIELDS
TWEET_BATCH_FIELDS = TWEET_ITEM_FIELDS + LABEL_FIELDS_COMMON + TWEET_SECONDARY_FIELDS
SARCASM_VALUES = ("yes", "no", "unsure")
TEXT_STATUS_PENDING = "NOT_MATERIALISED: rights/privacy clearance pending (see reports/INDIAN_DATA_PROVENANCE_AND_RIGHTS.md)"


def label_fields(kind: str) -> list[str]:
    return LABEL_FIELDS_COMMON + (MYGOV_SECONDARY_FIELDS if kind == "mygov" else TWEET_SECONDARY_FIELDS)


def is_annotated(row: dict, kind: str) -> bool:
    return any(str(row.get(f, "")).strip() for f in label_fields(kind))


def validate_label_row(row: dict, kind: str) -> list[str]:
    """Return problems for one row. A row with every label field blank is unannotated, not invalid."""
    g = lambda f: str(row.get(f, "")).strip()
    if not is_annotated(row, kind):
        return []
    p: list[str] = []
    stance, excl = g("stance"), g("exclusion_code")
    if stance == "Mixed":
        p.append("'Mixed' is a codebook-v1 label outside the 4-class scheme; use Unclear with unclear_reason = MIXED")
    elif stance.lower() in SENTIMENT_LIKE_VALUES:
        p.append(f"stance '{stance}' is a sentiment/polarity value, not a stance label")
    elif stance and stance not in STANCE_LABELS:
        p.append(f"stance '{stance}' not in {list(STANCE_LABELS)}")
    if excl and excl not in EXCLUSION_CODES:
        p.append(f"exclusion_code '{excl}' not in {list(EXCLUSION_CODES)}")
    if bool(stance) == bool(excl):
        p.append("exactly one of stance or exclusion_code must be set")
    if stance == "Unclear" and g("unclear_reason") not in UNCLEAR_REASONS:
        p.append(f"Unclear requires unclear_reason in {list(UNCLEAR_REASONS)}")
    if stance != "Unclear" and g("unclear_reason"):
        p.append("unclear_reason is only allowed with stance = Unclear")
    if g("confidence") not in CONFIDENCE_VALUES:
        p.append(f"confidence must be one of {list(CONFIDENCE_VALUES)}")
    if g("needs_review") not in NEEDS_REVIEW_VALUES:
        p.append("needs_review must be 'yes' or 'no'")
    if g("needs_review") == "yes" and g("needs_review_reason") not in NEEDS_REVIEW_REASONS:
        p.append(f"needs_review = yes requires needs_review_reason in {list(NEEDS_REVIEW_REASONS)}")
    if g("needs_review") == "no" and g("needs_review_reason"):
        p.append("needs_review_reason must be blank when needs_review = no")
    needs_rationale = stance in RATIONALE_REQUIRED_FOR_STANCE or bool(excl) or g("needs_review") == "yes"
    if needs_rationale and len(g("rationale").split()) < 3:
        p.append("rationale of at least 3 words required for Oppose, Unclear, exclusions and needs_review = yes")
    if not g("annotator_id"):
        p.append("annotator_id required")
    if kind == "tweets" and stance and not g("stance_target"):
        p.append("tweets require stance_target whenever a stance is given")
    if kind == "tweets" and g("sarcasm_or_irony") and g("sarcasm_or_irony") not in SARCASM_VALUES:
        p.append(f"sarcasm_or_irony must be one of {list(SARCASM_VALUES)}")
    return p

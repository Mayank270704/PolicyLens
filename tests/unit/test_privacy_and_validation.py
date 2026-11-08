from backend.app.services.privacy import scan_for_pii
from backend.app.services.validation import classify_comment_for_exclusion


# ---- PII scanning: flag-for-review, never a guarantee of anonymity --------

def test_pii_scan_flags_email():
    result = scan_for_pii("Contact me at jane.doe@example.com about this.")
    assert result.flagged
    assert "email_address_pattern" in result.reasons
    assert "[redacted-email]" in result.redacted_text
    assert "jane.doe@example.com" not in result.redacted_text


def test_pii_scan_flags_phone_number():
    result = scan_for_pii("Call me at 555-123-4567 if you have questions.")
    assert result.flagged
    assert "phone_number_like_pattern" in result.reasons


def test_pii_scan_clean_text_is_not_flagged():
    result = scan_for_pii("I support this policy because it improves transparency.")
    assert result.flagged is False
    assert result.redacted_text is None


def test_pii_scan_does_not_claim_anonymity_guarantee():
    """Per the task's explicit instruction: a clean scan must not be
    presented as a guarantee of anonymity. The disclaimer must exist and
    say so, regardless of any individual scan's result."""
    from backend.app.services.privacy import PiiScanResult

    assert "does NOT mean the text is anonymous" in PiiScanResult.DISCLAIMER


# ---- exclusion-code heuristic (candidate suggestion, not an assignment) ----

def test_classify_blank_text_as_too_short():
    assert classify_comment_for_exclusion("") == "TOO_SHORT_NONSUBSTANTIVE"
    assert classify_comment_for_exclusion("   ") == "TOO_SHORT_NONSUBSTANTIVE"


def test_classify_generic_filler_as_too_short():
    assert classify_comment_for_exclusion("ok") == "TOO_SHORT_NONSUBSTANTIVE"
    assert classify_comment_for_exclusion("n/a") == "TOO_SHORT_NONSUBSTANTIVE"


def test_classify_unintelligible_text():
    assert classify_comment_for_exclusion("asdkjf ##@@ 3993 !!!$$") == "UNINTELLIGIBLE"


def test_classify_substantive_short_comment_is_not_excluded():
    """A short but substantive comment ('No, too expensive.') must NOT be
    flagged for exclusion -- mirrors
    STANCE_ANNOTATION_GUIDELINES.md section 5's own example."""
    assert classify_comment_for_exclusion("No, too expensive.") is None


def test_classify_normal_comment_is_not_excluded():
    assert classify_comment_for_exclusion(
        "I believe this policy will meaningfully improve transparency in government operations."
    ) is None

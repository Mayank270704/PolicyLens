"""PII detection integration point (requirement: Phase 7 security/privacy).

This is a regex-based heuristic flagger, not a certified anonymization
system. It is explicitly a FLAG-FOR-HUMAN-REVIEW step
(docs/architecture/SYSTEM_ARCHITECTURE.md component 3), not a guarantee.

IMPORTANT, per the task's own instruction: do not claim complete
anonymity merely because direct identifiers have been removed. A comment
with no email/phone match can still be re-identifying (a named local
official, a specific unique anecdote, etc.) -- this module says so
explicitly in its own docstrings and return values, rather than letting
"pii_flagged=False" be misread as "verified anonymous."
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"(\+?\d[\d\-\s().]{7,}\d)")
_SSN_LIKE_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")  # US SSN format, as one example of a structured identifier


@dataclass
class PiiScanResult:
    flagged: bool
    reasons: list[str] = field(default_factory=list)
    redacted_text: str | None = None

    DISCLAIMER = (
        "This scan only matches a few structured patterns (email, phone-like digit runs, "
        "SSN-like numbers). flagged=False does NOT mean the text is anonymous -- it may still "
        "contain names, locations, or unique anecdotes that are re-identifying. This is a "
        "flag-for-human-review tool, not a certified anonymization system."
    )


def scan_for_pii(text: str) -> PiiScanResult:
    reasons: list[str] = []
    redacted = text

    if _EMAIL_RE.search(text):
        reasons.append("email_address_pattern")
        redacted = _EMAIL_RE.sub("[redacted-email]", redacted)
    if _PHONE_RE.search(text):
        reasons.append("phone_number_like_pattern")
        redacted = _PHONE_RE.sub("[redacted-phone]", redacted)
    if _SSN_LIKE_RE.search(text):
        reasons.append("ssn_like_pattern")
        redacted = _SSN_LIKE_RE.sub("[redacted-id-number]", redacted)

    flagged = bool(reasons)
    return PiiScanResult(
        flagged=flagged,
        reasons=reasons,
        redacted_text=redacted if flagged else None,
    )

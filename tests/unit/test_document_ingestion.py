import io

import pytest

from backend.app.documents.extraction import HtmlExtractor, PdfExtractor, PlainTextExtractor, get_extractor
from backend.app.documents.ingestion import DocumentValidationError, ingest_policy_document, validate_upload
from backend.app.documents.sections import identify_sections
from backend.app.models.enums import DocumentProcessingStatus
from backend.app.models.policy import PolicyDocument, PolicySection


# ---- file validation --------------------------------------------------------

def test_validate_upload_accepts_supported_extension():
    ext = validate_upload("policy.txt", b"some content")
    assert ext == ".txt"


def test_validate_upload_rejects_unsupported_extension():
    with pytest.raises(DocumentValidationError, match="Unsupported file type"):
        validate_upload("policy.docx", b"some content")


def test_validate_upload_rejects_empty_file():
    with pytest.raises(DocumentValidationError, match="empty"):
        validate_upload("policy.txt", b"")


def test_validate_upload_rejects_oversized_file():
    from backend.app.config import MAX_UPLOAD_SIZE_BYTES

    with pytest.raises(DocumentValidationError, match="exceeds"):
        validate_upload("policy.txt", b"x" * (MAX_UPLOAD_SIZE_BYTES + 1))


# ---- text extraction --------------------------------------------------------

def test_plain_text_extractor_utf8():
    result = PlainTextExtractor().extract("Hello, policy world.".encode("utf-8"))
    assert result.success
    assert result.text == "Hello, policy world."


def test_plain_text_extractor_falls_back_to_latin1():
    raw = "café".encode("latin-1")
    result = PlainTextExtractor().extract(raw)
    assert result.success


def test_html_extractor_strips_tags_and_scripts():
    html = b"<html><body><script>evil()</script><h1>Title</h1><p>Body text.</p></body></html>"
    result = HtmlExtractor().extract(html)
    assert result.success
    assert "Title" in result.text
    assert "Body text." in result.text
    assert "evil()" not in result.text


def test_pdf_extractor_reports_failure_on_garbage_bytes():
    result = PdfExtractor().extract(b"this is not a real pdf file")
    assert result.success is False
    assert result.error is not None


def test_pdf_extractor_reports_failure_on_blank_page_pdf():
    """A structurally valid PDF with no extractable text (e.g. a blank
    or scanned/image-only page) must be reported as a failure with a
    clear reason, not silently return empty text as if it were fine."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)

    result = PdfExtractor().extract(buf.getvalue())
    assert result.success is False
    assert "scanned/image-only" in result.error


def test_get_extractor_unknown_extension_returns_none():
    assert get_extractor(".docx") is None


# ---- section identification (heuristic) ------------------------------------

def test_identify_sections_with_numbered_headings():
    text = "Section 1. Transparency\nGovernment must be transparent.\n\nSection 2. Accountability\nGovernment must be accountable."
    sections = identify_sections(text)
    assert len(sections) == 2
    assert sections[0].label == "Section 1. Transparency"
    assert sections[1].label == "Section 2. Accountability"
    assert sections[0].order_index == 0
    assert sections[1].order_index == 1


def test_identify_sections_falls_back_to_whole_document():
    text = "Just a single paragraph of policy text with no heading structure at all."
    sections = identify_sections(text)
    assert len(sections) == 1
    assert sections[0].label == "Whole document"
    assert sections[0].text == text


def test_identify_sections_empty_text_returns_nothing():
    assert identify_sections("") == []
    assert identify_sections("   ") == []


# ---- ingestion orchestration: versioning + error reporting -----------------

def test_ingest_creates_version_and_sections(db_session):
    policy = PolicyDocument(title="P")
    db_session.add(policy)
    db_session.commit()

    result = ingest_policy_document(
        db_session, policy.id, "policy.txt",
        b"Section 1. Intro\nSome text.\n\nSection 2. Details\nMore text.",
    )
    assert result.status == DocumentProcessingStatus.PROCESSED
    assert result.sections_created == 2
    assert result.version.version_number == 1

    sections = db_session.query(PolicySection).filter_by(policy_document_id=policy.id).all()
    assert len(sections) == 2
    assert all(s.policy_document_version_id == result.version.id for s in sections)


def test_reingesting_creates_a_new_version_not_an_overwrite(db_session):
    policy = PolicyDocument(title="P")
    db_session.add(policy)
    db_session.commit()

    r1 = ingest_policy_document(db_session, policy.id, "v1.txt", b"Original content.")
    r2 = ingest_policy_document(db_session, policy.id, "v2.txt", b"Section 1. Revised\nRevised content.")

    assert r1.version.version_number == 1
    assert r2.version.version_number == 2
    assert r1.version.raw_text == "Original content."  # first version's text is untouched by the second ingest

    all_sections = db_session.query(PolicySection).filter_by(policy_document_id=policy.id).all()
    # both versions' sections coexist -- nothing was deleted or overwritten
    assert any(s.policy_document_version_id == r1.version.id for s in all_sections)
    assert any(s.policy_document_version_id == r2.version.id for s in all_sections)


def test_ingest_reports_failure_for_unparseable_pdf(db_session):
    policy = PolicyDocument(title="P")
    db_session.add(policy)
    db_session.commit()

    result = ingest_policy_document(db_session, policy.id, "bad.pdf", b"not a real pdf")
    assert result.status == DocumentProcessingStatus.FAILED
    assert result.error is not None
    assert result.version.raw_text == ""  # no partial/garbage text stored

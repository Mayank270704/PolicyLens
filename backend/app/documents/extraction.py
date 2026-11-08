"""Text extraction for supported policy-document formats.

Only uses libraries already present in this environment (pypdf,
beautifulsoup4) -- nothing new was installed for this. Plain-text and
HTML extraction use the Python standard library plus bs4; PDF extraction
uses pypdf.
"""
from __future__ import annotations

import io
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    text: str
    success: bool
    error: str | None = None


class TextExtractor(ABC):
    @abstractmethod
    def extract(self, raw_bytes: bytes) -> ExtractionResult: ...


class PlainTextExtractor(TextExtractor):
    def extract(self, raw_bytes: bytes) -> ExtractionResult:
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = raw_bytes.decode("latin-1")
            except Exception as e:  # pragma: no cover - extremely unlikely
                return ExtractionResult(text="", success=False, error=f"decode failed: {e}")
        return ExtractionResult(text=text, success=True)


class HtmlExtractor(TextExtractor):
    def extract(self, raw_bytes: bytes) -> ExtractionResult:
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(raw_bytes, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n").strip()
            return ExtractionResult(text=text, success=True)
        except Exception as e:
            return ExtractionResult(text="", success=False, error=str(e))


class PdfExtractor(TextExtractor):
    def extract(self, raw_bytes: bytes) -> ExtractionResult:
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(raw_bytes))
            pages_text = [page.extract_text() or "" for page in reader.pages]
            text = "\n\n".join(pages_text).strip()
            if not text:
                return ExtractionResult(
                    text="", success=False,
                    error="pypdf extracted no text -- likely a scanned/image-only PDF; OCR is not implemented",
                )
            return ExtractionResult(text=text, success=True)
        except Exception as e:
            return ExtractionResult(text="", success=False, error=str(e))


_EXTRACTORS: dict[str, TextExtractor] = {
    ".txt": PlainTextExtractor(),
    ".html": HtmlExtractor(),
    ".htm": HtmlExtractor(),
    ".pdf": PdfExtractor(),
}


def get_extractor(file_extension: str) -> TextExtractor | None:
    return _EXTRACTORS.get(file_extension.lower())

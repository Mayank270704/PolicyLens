"""Section identification -- a heuristic, not a robust parser.

Real policy documents vary wildly in structure (numbered clauses, markdown
headings, plain paragraphs, or -- as this project's own real corpus shows,
see docs/dataset/SINGLE_ANNOTATOR_PROTOCOL.md section 5 -- no formal
section structure at all). This module makes a best-effort attempt and
falls back to a single whole-document section when it can't find
anything more specific, exactly matching docs/architecture/DATA_MODEL.md's
documented accommodation for that real situation. This heuristic nature is
stated here explicitly, not left implicit, per
docs/experiments/RESEARCH_LIMITATIONS.md's standard of honesty about scope.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING_RE = re.compile(
    r"^(?:#{1,6}\s+.+|(?:Section|Article|Clause|Part)\s+\d+[a-zA-Z.:)]*.*|\d+(?:\.\d+)*\.?\s+[A-Z].{3,100})$",
    re.MULTILINE,
)


@dataclass
class IdentifiedSection:
    label: str
    text: str
    order_index: int


def identify_sections(document_text: str) -> list[IdentifiedSection]:
    matches = list(_HEADING_RE.finditer(document_text))
    if not matches:
        stripped = document_text.strip()
        if not stripped:
            return []
        return [IdentifiedSection(label="Whole document", text=stripped, order_index=0)]

    sections: list[IdentifiedSection] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(document_text)
        label = match.group(0).strip()
        body = document_text[start:end].strip()
        if body:
            sections.append(IdentifiedSection(label=label[:300], text=body, order_index=i))
    return sections

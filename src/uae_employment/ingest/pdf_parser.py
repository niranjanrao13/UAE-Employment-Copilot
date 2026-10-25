from __future__ import annotations

import hashlib
from io import BytesIO

from pypdf import PdfReader

from ..models import Section


def parse_pdf_pages(source_id: str, body: bytes) -> tuple[str | None, list[Section]]:
    reader = PdfReader(BytesIO(body))
    title = None
    if reader.metadata:
        title = getattr(reader.metadata, "title", None)

    sections: list[Section] = []
    running_char = 0
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        start = running_char
        end = start + len(text)
        running_char = end + 1
        sections.append(
            Section(
                section_id=f"{source_id}:page:{i + 1:04d}",
                source_id=source_id,
                ordinal=i,
                heading=f"Page {i + 1}",
                text=text,
                sha256=digest,
                char_start=start,
                char_end=end,
            )
        )
    return title, sections

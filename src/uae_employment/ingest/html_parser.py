from __future__ import annotations

import hashlib
import re

from bs4 import BeautifulSoup, Tag

from ..models import Section


DROP_TAGS = {"script", "style", "noscript", "svg", "iframe", "form"}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def _clean(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_html_sections(source_id: str, html: bytes) -> tuple[str | None, list[Section]]:
    soup = BeautifulSoup(html, "lxml")
    title = _clean(soup.title.get_text(" ", strip=True)) if soup.title else None

    for tag in soup.find_all(DROP_TAGS):
        tag.decompose()

    main = soup.find("main") or soup.find(attrs={"role": "main"}) or soup.body or soup
    heading_nodes = [h for h in main.find_all(HEADING_TAGS) if _clean(h.get_text(" ", strip=True))]

    sections: list[Section] = []
    running_char = 0

    if not heading_nodes:
        text = _clean(main.get_text("\n", strip=True))
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return title, [
            Section(
                section_id=f"{source_id}:0000",
                source_id=source_id,
                ordinal=0,
                heading="Document",
                text=text,
                sha256=digest,
                char_start=0,
                char_end=len(text),
            )
        ]

    for ordinal, heading in enumerate(heading_nodes):
        heading_text = _clean(heading.get_text(" ", strip=True))
        chunks: list[str] = []

        for sibling in heading.next_siblings:
            if isinstance(sibling, Tag) and sibling.name in HEADING_TAGS:
                break
            if isinstance(sibling, Tag):
                text = _clean(sibling.get_text("\n", strip=True))
            else:
                text = _clean(str(sibling))
            if text:
                chunks.append(text)

        text = _clean("\n".join(chunks))
        if not text:
            continue

        digest = hashlib.sha256((heading_text + "\n" + text).encode("utf-8")).hexdigest()
        start = running_char
        end = start + len(text)
        running_char = end + 1
        sections.append(
            Section(
                section_id=f"{source_id}:{ordinal:04d}",
                source_id=source_id,
                ordinal=ordinal,
                heading=heading_text,
                text=text,
                sha256=digest,
                char_start=start,
                char_end=end,
            )
        )

    return title, sections

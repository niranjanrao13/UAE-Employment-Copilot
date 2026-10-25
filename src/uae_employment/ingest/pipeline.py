from __future__ import annotations

import json
from pathlib import Path

from ..facts.deterministic import extract_structured_service_facts
from ..models import ParserType, SourceDocument, SourceSpec
from .fetch import fetch_source
from .html_parser import parse_html_sections
from .pdf_parser import parse_pdf_pages


def _write_jsonl(path: Path, records: list) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")


def ingest_source(source: SourceSpec, raw_root: Path, processed_root: Path) -> dict[str, int | str]:
    body, fetch = fetch_source(source, raw_root)

    if source.parser == ParserType.HTML:
        detected_title, sections = parse_html_sections(source.id, body)
    else:
        detected_title, sections = parse_pdf_pages(source.id, body)

    document = SourceDocument(
        source=source,
        fetch=fetch,
        title_detected=detected_title,
        text_length=sum(len(s.text) for s in sections),
        section_count=len(sections),
    )

    facts = extract_structured_service_facts(document, sections)

    processed_root.mkdir(parents=True, exist_ok=True)
    document_path = processed_root / f"{source.id}.document.json"
    sections_path = processed_root / f"{source.id}.sections.jsonl"
    facts_path = processed_root / f"{source.id}.facts.jsonl"

    document_path.write_text(document.model_dump_json(indent=2), encoding="utf-8")
    _write_jsonl(sections_path, sections)
    _write_jsonl(facts_path, facts)

    return {
        "source_id": source.id,
        "sections": len(sections),
        "facts": len(facts),
        "sha256": fetch.sha256,
    }

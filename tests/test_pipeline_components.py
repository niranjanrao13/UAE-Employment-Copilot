from pathlib import Path

from uae_employment.facts.deterministic import extract_structured_service_facts
from uae_employment.ingest.html_parser import parse_html_sections
from uae_employment.models import FetchMetadata, SourceDocument, SourceSpec


def test_html_parser_and_deterministic_facts():
    fixture = Path(__file__).parent / "fixtures" / "mohre_service.html"
    title, sections = parse_html_sections("mohre_permit_temporary", fixture.read_bytes())
    assert title == "Temporary Work Permit"
    assert any(s.heading == "Permit Duration" and "6 months" in s.text for s in sections)

    source = SourceSpec.model_validate({
        "id": "mohre_permit_temporary",
        "title": "Temporary permit",
        "authority": "MOHRE",
        "source_type": "service_page",
        "language": "en",
        "url": "https://example.com",
        "priority": 1,
        "parser": "html",
        "domain": "work_permits",
    })
    fetch = FetchMetadata.model_validate({
        "retrieved_at": "2026-09-11T00:00:00Z",
        "status_code": 200,
        "content_type": "text/html",
        "sha256": "abc123",
        "raw_path": "data/raw/test.html",
    })
    document = SourceDocument(source=source, fetch=fetch, title_detected=title, section_count=len(sections))
    facts = extract_structured_service_facts(document, sections)

    assert any(f.predicate == "permit_duration" and f.object_value == "6 months" for f in facts)
    assert any(f.predicate == "service_fee" and "50 dirhams" in f.object_value for f in facts)
    assert all(f.evidence_text for f in facts)

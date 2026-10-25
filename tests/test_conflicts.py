from uae_employment.facts.conflicts import audit_bilingual_conflicts
from uae_employment.models import CanonicalFact, SourceSpec, Verification


def _source(source_id: str, language: str):
    return SourceSpec.model_validate({
        "id": source_id,
        "title": source_id,
        "authority": "MOHRE",
        "source_type": "service_page",
        "language": language,
        "url": f"https://example.com/{source_id}",
        "priority": 1,
        "parser": "html",
        "domain": "work_permits",
        "canonical_group": "mission",
    })


def _fact(source_id: str, value: str):
    return CanonicalFact(
        fact_id=f"fact_{source_id}",
        source_id=source_id,
        section_id=f"{source_id}:1",
        domain="work_permits",
        subject="mission",
        predicate="permit_duration",
        object_value=value,
        evidence_text=value,
        extraction_method="deterministic_html_structure",
        source_sha256="abc",
        verification=Verification(),
    )


def test_bilingual_duration_conflict_is_quarantined():
    sources = [_source("mission_en", "en"), _source("mission_ar", "ar")]
    facts = {
        "mission_en": [_fact("mission_en", "Three months, renewable once for a similar period")],
        "mission_ar": [_fact("mission_ar", "سنتين")],
    }
    conflicts = audit_bilingual_conflicts(sources, facts)
    assert len(conflicts) == 1
    assert conflicts[0]["status"] == "QUARANTINE"
    assert {o["normalized_value"] for o in conflicts[0]["observations"]} == {3, 24}

from __future__ import annotations

import hashlib
import re

from ..models import CanonicalFact, Section, SourceDocument, Verification


HEADING_PREDICATES = {
    "permit duration": "permit_duration",
    "service completion duration": "service_completion_duration",
    "type of employment contracts": "employment_contract_types",
    "target audience": "target_audience",
    "conditions & requirements": "condition_or_requirement",
    "conditions and requirements": "condition_or_requirement",
    "required documents": "required_document",
    "service fees": "service_fee",
    "service channels": "service_channel",
    "مدة التصريح": "permit_duration",
    "مدة إتمام الخدمة": "service_completion_duration",
    "أنماط العمل المقررة": "employment_contract_types",
    "الجمهور المستهدف": "target_audience",
    "الشروط والمتطلبات": "condition_or_requirement",
    "المستندات المطلوبة": "required_document",
    "رسوم الخدمة": "service_fee",
    "قنوات تقديم الخدمة": "service_channel",
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _items(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        item = re.sub(r"^\s*(?:[-*]|\d+[.)]?)\s*", "", raw).strip()
        if item and item not in {"* * *"}:
            lines.append(item)
    return lines or [text.strip()]


def extract_structured_service_facts(document: SourceDocument, sections: list[Section]) -> list[CanonicalFact]:
    if document.source.source_type.value != "service_page":
        return []

    facts: list[CanonicalFact] = []
    subject = document.source.id.removeprefix("mohre_")

    for section in sections:
        key = section.heading.strip().lower().rstrip(":")
        predicate = HEADING_PREDICATES.get(key)
        if not predicate:
            continue

        values = _items(section.text) if predicate in {
            "condition_or_requirement", "required_document", "service_fee", "service_channel"
        } else [section.text.strip()]

        for item_index, value in enumerate(values):
            if not value:
                continue
            raw_id = f"{document.source.id}|{section.section_id}|{predicate}|{item_index}|{value}"
            fact_id = "FACT_" + hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:16].upper()
            rules = ["heading_to_predicate_map", "exact_evidence_retained"]
            if re.search(r"\d", value):
                rules.append("numeric_surface_form_retained")

            facts.append(
                CanonicalFact(
                    fact_id=fact_id,
                    source_id=document.source.id,
                    section_id=section.section_id,
                    domain=document.source.domain,
                    subject=_slug(subject),
                    predicate=predicate,
                    object_value=value,
                    evidence_text=value,
                    extraction_method="deterministic_html_structure",
                    source_sha256=document.fetch.sha256,
                    verification=Verification(deterministic_pass=True, rules=rules),
                )
            )
    return facts

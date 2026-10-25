from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..models import CanonicalFact, SourceSpec


ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "واحد": 1, "واحدة": 1, "اثنان": 2, "اثنين": 2, "سنتين": 2,
    "ثلاث": 3, "ثلاثة": 3, "أربع": 4, "اربعة": 4, "خمسة": 5, "ستة": 6,
}


def _duration_months(text: str) -> int | None:
    t = text.translate(ARABIC_DIGITS).lower()
    number = None
    match = re.search(r"\b(\d+)\b", t)
    if match:
        number = int(match.group(1))
    else:
        for word, value in NUMBER_WORDS.items():
            if word in t:
                number = value
                break
    if number is None:
        return None

    if any(unit in t for unit in ["year", "years", "سنة", "سنوات", "سنتين"]):
        return number * 12
    if any(unit in t for unit in ["month", "months", "شهر", "أشهر", "اشهر"]):
        return number
    return None


def normalized_value(fact: CanonicalFact) -> Any:
    if fact.predicate == "permit_duration":
        return _duration_months(fact.object_value)
    return None


def audit_bilingual_conflicts(
    sources: list[SourceSpec], facts_by_source: dict[str, list[CanonicalFact]]
) -> list[dict[str, Any]]:
    groups: dict[str, list[SourceSpec]] = defaultdict(list)
    for source in sources:
        if source.canonical_group:
            groups[source.canonical_group].append(source)

    conflicts: list[dict[str, Any]] = []
    for group_id, group_sources in groups.items():
        if len({s.language for s in group_sources}) < 2:
            continue
        values: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for source in group_sources:
            for fact in facts_by_source.get(source.id, []):
                value = normalized_value(fact)
                if value is not None:
                    values[fact.predicate].append({
                        "source_id": source.id,
                        "language": source.language,
                        "raw_value": fact.object_value,
                        "normalized_value": value,
                        "fact_id": fact.fact_id,
                    })
        for predicate, items in values.items():
            distinct = {item["normalized_value"] for item in items}
            if len(distinct) > 1:
                conflicts.append({
                    "canonical_group": group_id,
                    "predicate": predicate,
                    "status": "QUARANTINE",
                    "reason": "bilingual_authoritative_sources_disagree",
                    "observations": items,
                })
    return conflicts


def load_facts(path: Path) -> list[CanonicalFact]:
    if not path.exists():
        return []
    return [CanonicalFact.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_conflicts(path: Path, conflicts: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(conflicts, ensure_ascii=False, indent=2), encoding="utf-8")

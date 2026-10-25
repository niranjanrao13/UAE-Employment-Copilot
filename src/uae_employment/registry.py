from pathlib import Path

import yaml
from pydantic import TypeAdapter

from .models import SourceSpec


SOURCE_LIST = TypeAdapter(list[SourceSpec])


def load_sources(path: Path) -> list[SourceSpec]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SOURCE_LIST.validate_python(payload["sources"])


def get_source(path: Path, source_id: str) -> SourceSpec:
    for source in load_sources(path):
        if source.id == source_id:
            return source
    raise KeyError(f"Unknown source_id: {source_id}")

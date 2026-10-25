from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class Authority(StrEnum):
    UAE_LEGISLATION = "UAE_LEGISLATION"
    MOHRE = "MOHRE"
    UAE_PORTAL = "UAE_PORTAL"


class SourceType(StrEnum):
    LEGAL_TEXT = "legal_text"
    SERVICE_PAGE = "service_page"
    GUIDANCE_PAGE = "guidance_page"


class ParserType(StrEnum):
    HTML = "html"
    PDF = "pdf"


class SourceSpec(BaseModel):
    id: str
    title: str
    authority: Authority
    source_type: SourceType
    language: str = "en"
    url: HttpUrl
    priority: int = 1
    parser: ParserType
    domain: str
    canonical_group: str | None = None


class FetchMetadata(BaseModel):
    retrieved_at: datetime
    status_code: int
    content_type: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    sha256: str
    raw_path: str


class SourceDocument(BaseModel):
    source: SourceSpec
    fetch: FetchMetadata
    title_detected: str | None = None
    text_length: int = 0
    section_count: int = 0


class Section(BaseModel):
    section_id: str
    source_id: str
    ordinal: int
    heading: str
    text: str
    sha256: str
    char_start: int = 0
    char_end: int = 0


class Verification(BaseModel):
    deterministic_pass: bool = True
    rules: list[str] = Field(default_factory=list)
    llm_verifiers: list[dict[str, Any]] = Field(default_factory=list)


class CanonicalFact(BaseModel):
    fact_id: str
    source_id: str
    section_id: str
    domain: str
    canonical_group: str | None = None
    subject: str
    predicate: str
    object_value: str
    object_unit: str | None = None
    qualifiers: dict[str, Any] = Field(default_factory=dict)
    evidence_text: str
    extraction_method: str
    source_sha256: str
    verification: Verification

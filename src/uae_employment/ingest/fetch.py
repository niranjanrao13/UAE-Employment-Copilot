from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from ..models import FetchMetadata, SourceSpec


USER_AGENT = (
    "Mozilla/5.0 (compatible; UAEEmploymentResearchBot/0.1; "
    "+non-commercial research project)"
)


def fetch_source(source: SourceSpec, raw_root: Path, attempts: int = 3) -> tuple[bytes, FetchMetadata]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en,ar;q=0.8",
    }

    last_error: Exception | None = None
    response: httpx.Response | None = None
    for attempt in range(attempts):
        try:
            with httpx.Client(follow_redirects=True, timeout=45.0, headers=headers) as client:
                response = client.get(str(source.url))
                response.raise_for_status()
            break
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            last_error = exc
            if attempt == attempts - 1:
                raise
            time.sleep(2**attempt)

    if response is None:
        raise RuntimeError("Fetch failed without a response") from last_error

    body = response.content
    digest = hashlib.sha256(body).hexdigest()
    content_type = response.headers.get("content-type")

    suffix = ".pdf" if ("pdf" in (content_type or "").lower() or source.parser.value == "pdf") else ".html"
    target_dir = raw_root / source.id
    target_dir.mkdir(parents=True, exist_ok=True)
    raw_path = target_dir / f"{digest}{suffix}"
    raw_path.write_bytes(body)

    metadata = FetchMetadata(
        retrieved_at=datetime.now(timezone.utc),
        status_code=response.status_code,
        content_type=content_type,
        etag=response.headers.get("etag"),
        last_modified=response.headers.get("last-modified"),
        sha256=digest,
        raw_path=str(raw_path),
    )
    return body, metadata

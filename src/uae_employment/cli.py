from __future__ import annotations

from pathlib import Path

import typer

from .facts.conflicts import audit_bilingual_conflicts, load_facts, write_conflicts
from .ingest.pipeline import ingest_source
from .registry import get_source, load_sources

app = typer.Typer(no_args_is_help=True)
ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "config" / "sources.yaml"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"


@app.command("sources")
def sources() -> None:
    """List registered authoritative sources."""
    for source in load_sources(REGISTRY):
        typer.echo(
            f"{source.id:32} priority={source.priority} parser={source.parser.value:4} "
            f"authority={source.authority.value:15} {source.title}"
        )


@app.command("ingest")
def ingest(
    source_id: str | None = typer.Option(None, help="Ingest exactly one source ID."),
    html_only: bool = typer.Option(False, help="Ingest all HTML sources only."),
) -> None:
    """Fetch and parse sources, retaining complete provenance."""
    all_sources = load_sources(REGISTRY)
    if source_id:
        selected = [get_source(REGISTRY, source_id)]
    elif html_only:
        selected = [s for s in all_sources if s.parser.value == "html"]
    else:
        raise typer.BadParameter("Use --source-id SOURCE or --html-only for the first milestone.")

    for source in selected:
        result = ingest_source(source, RAW, PROCESSED)
        typer.echo(
            f"{result['source_id']}: sections={result['sections']} facts={result['facts']} "
            f"sha256={str(result['sha256'])[:12]}..."
        )


@app.command("audit-conflicts")
def audit_conflicts() -> None:
    """Compare paired Arabic/English facts and quarantine deterministic disagreements."""
    all_sources = load_sources(REGISTRY)
    facts_by_source = {
        source.id: load_facts(PROCESSED / f"{source.id}.facts.jsonl")
        for source in all_sources
    }
    conflicts = audit_bilingual_conflicts(all_sources, facts_by_source)
    out = PROCESSED / "bilingual_conflicts.json"
    PROCESSED.mkdir(parents=True, exist_ok=True)
    write_conflicts(out, conflicts)
    typer.echo(f"conflicts={len(conflicts)} output={out}")
    for item in conflicts:
        typer.echo(f"QUARANTINE {item['canonical_group']} {item['predicate']}")


if __name__ == "__main__":
    app()

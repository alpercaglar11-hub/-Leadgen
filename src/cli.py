"""CLI entry points.

Usage:
    python -m src.cli scrape
    python -m src.cli outreach
    python -m src.cli status
"""

from __future__ import annotations

import logging
import sys

import click

from src import get_logger, settings
from src.db import Lead, Session, init_db

try:
    import sentry_sdk  # noqa: F811
except ImportError:
    sentry_sdk = None  # type: ignore[assignment]

log = get_logger(__name__)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable DEBUG logging")
def cli(verbose: bool) -> None:
    level = logging.DEBUG if verbose else getattr(logging, settings.log_level)
    logging.getLogger().setLevel(level)


@cli.command()
@click.argument("query", required=False, default="")
@click.option("--limit", "-l", default=10, type=int, help="Max leads to collect")
def scrape(query: str, limit: int) -> None:
    """Search Google for leads matching QUERY and save to database."""
    if not query:
        click.echo("Usage: python -m src.cli scrape \"Digital Agencies in Brno\" --limit 10")
        sys.exit(1)
    init_db()
    from src.core.scraper import scrape_google, save_leads_to_db
    try:
        leads = scrape_google(query, limit=limit)
    except Exception as exc:
        if sentry_sdk:
            sentry_sdk.capture_exception(exc)
        click.echo(f"Scrape failed: {exc}", err=True)
        sys.exit(1)
    saved = save_leads_to_db(leads, query)
    click.echo(f"Found {len(leads)} leads, saved {saved} new to database.")
    sys.exit(0)


@cli.command()
@click.option("--limit", "-l", default=5, type=int, help="Max leads to process")
@click.option("--dry-run/--no-dry-run", default=True, help="Simulate without sending")
def outreach(limit: int, dry_run: bool) -> None:
    """Send personalized cold emails to qualified leads."""
    init_db()
    from src.core.outreach import run_outreach
    result = run_outreach(limit=limit, dry_run=dry_run)
    click.echo(f"Sent: {result.sent}, Skipped: {result.skipped}, Failed: {result.failed}")
    if result.errors:
        click.echo(f"Errors ({len(result.errors)}):", err=True)
        for e in result.errors:
            click.echo(f"  - {e}", err=True)
    sys.exit(1 if result.failed > 0 else 0)


@cli.command()
def status() -> None:
    """Show lead database status."""
    init_db()
    with Session() as sess:
        total = sess.query(Lead).count()
        contacted = sess.query(Lead).filter(
            Lead.outreach_stage.in_(["contacted", "replied", "converted"])
        ).count()
    click.echo(f"Total leads: {total}")
    click.echo(f"Contacted:   {contacted}")
    sys.exit(0)


@cli.command()
def init_db_cmd() -> None:
    """Create database tables."""
    init_db()
    click.echo("Database tables created.")


@cli.command()
def run() -> None:
    """Run one full agent cycle: housekeeping, scrape, outreach."""
    init_db()
    from src.core.orchestrator import run as run_cycle
    run_cycle()
    sys.exit(0)


if __name__ == "__main__":
    cli()

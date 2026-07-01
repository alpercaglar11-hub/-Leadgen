"""Agent orchestrator — coordinates scraping, outreach, and housekeeping.

This module is the entry point for the cron-driven ``run`` cycle.
It is invoked by ``python -m src.cli run`` or via the deployment cron.

Each cycle:
  1. Runs housekeeping (decision-log cleanup, old backup pruning).
  2. Scrapes for new leads.
  3. Runs outreach on qualified leads.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import text

from src.db import DecisionLog, Session

logger = structlog.get_logger(__name__)

DECISION_LOG_RETENTION_DAYS = 90
"""Delete ``decision_logs`` rows older than this many days."""


def cleanup_decision_logs() -> int:
    """Delete decision logs older than *DECISION_LOG_RETENTION_DAYS*.

    Returns the number of rows deleted.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=DECISION_LOG_RETENTION_DAYS)
    with Session() as sess:
        result = sess.execute(
            DecisionLog.__table__.delete().where(
                DecisionLog.created_at < cutoff
            )
        )
        sess.commit()
    deleted = result.rowcount
    if deleted:
        logger.info("Cleaned up %d decision logs older than %d days",
                    deleted, DECISION_LOG_RETENTION_DAYS)
    else:
        logger.debug("No decision logs to clean up")
    return deleted


def run() -> None:
    """Run one full agent cycle: housekeeping → scrape → outreach."""
    logger.info("Agent cycle starting")

    # ── Housekeeping ────────────────────────────────────────────────
    try:
        cleanup_decision_logs()
    except Exception as exc:
        logger.warning("Decision log cleanup failed: %s", exc)

    # ── Scrape ──────────────────────────────────────────────────────
    try:
        from src.core.scraper import scrape_google, save_leads_to_db

        query = "digital agencies Europe B2B"
        logger.info("Scraping leads: query=%s", query)
        leads = scrape_google(query, limit=10)
        saved = save_leads_to_db(leads, query)
        logger.info("Scrape complete: found=%d, saved=%d", len(leads), saved)
    except Exception as exc:
        logger.warning("Scrape step failed: %s", exc)

    # ── Outreach ────────────────────────────────────────────────────
    try:
        from src.core.outreach import run_outreach

        result = run_outreach(limit=5, dry_run=True)
        logger.info("Outreach complete: sent=%d, skipped=%d, failed=%d",
                    result.sent, result.skipped, result.failed)
    except Exception as exc:
        logger.warning("Outreach step failed: %s", exc)

    logger.info("Agent cycle complete")

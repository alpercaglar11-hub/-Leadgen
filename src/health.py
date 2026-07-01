from __future__ import annotations

from dataclasses import dataclass

import structlog
from sqlalchemy import text

from src.db import Session, init_db

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    message: str = ""


def check_database() -> CheckResult:
    try:
        with Session() as sess:
            sess.execute(text("SELECT 1"))
        return CheckResult(name="database", ok=True, message="Connected")
    except Exception as exc:
        return CheckResult(name="database", ok=False, message=f"Cannot connect: {exc}")


def check_browser() -> CheckResult:
    try:
        from src.browser.kimi import KimiBrowser
        b = KimiBrowser()
        if b.check_available():
            return CheckResult(name="browser", ok=True, message="Kimi WebBridge reachable")
        return CheckResult(name="browser", ok=False, message="Kimi WebBridge unreachable")
    except Exception as exc:
        return CheckResult(name="browser", ok=False, message=str(exc))


def run_checks() -> list[CheckResult]:
    checks = [check_database(), check_browser()]
    ok_count = sum(1 for c in checks if c.ok)
    for c in checks:
        if c.ok:
            logger.info("✅ %s — %s", c.name, c.message or "OK")
        else:
            logger.warning("❌ %s — %s", c.name, c.message)
    logger.info("Startup checks: %d passed, %d failed", ok_count, len(checks) - ok_count)
    return checks

"""LeadGen Agent — autonomous B2B lead generation and outreach."""

from __future__ import annotations

import logging as _logging
import sys

import structlog

from src.config import settings

# ── Sentry (optional — only initializes if SENTRY_DSN is set) ────────
if settings.sentry_dsn:
    import sentry_sdk  # noqa: F811

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.1,
        environment="production" if settings.sentry_dsn else "development",
        send_default_pii=False,
    )

_TIMESTAMPER = structlog.processors.TimeStamper(fmt="iso")


def _setup_structlog(log_level: str = "INFO") -> None:
    structlog.configure_once(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            _TIMESTAMPER,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    handler = _logging.StreamHandler(sys.stdout)
    if sys.stdout.isatty():
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(),
            ]
        )
    else:
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ]
        )
    handler.setFormatter(formatter)
    root = _logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(_logging, log_level.upper(), _logging.INFO))


_setup_structlog(log_level=settings.log_level)
get_logger = structlog.stdlib.get_logger
logger = get_logger(__name__)

__all__ = ["get_logger", "logger", "settings"]

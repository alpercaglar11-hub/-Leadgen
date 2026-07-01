"""Tests for the database models."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from src.db import Lead, LeadList, DecisionLog, Task, Session, init_db


class TestLead:
    def test_create_lead(self):
        with Session() as sess:
            lead = Lead(
                source="test_source",
                company_name="Test Corp",
                email="test@corp.com",
            )
            sess.add(lead)
            sess.commit()
            assert lead.id is not None
            assert lead.outreach_stage == "new"

    def test_lead_defaults(self):
        with Session() as sess:
            lead = Lead(source="directory", company_name="Acme")
            sess.add(lead)
            sess.commit()
            assert lead.outreach_stage == "new"
            assert lead.phone is None


class TestDecisionLog:
    def test_create_decision(self):
        with Session() as sess:
            d = DecisionLog(
                decision_type="scrape",
                reasoning="Found 5 leads on page 1",
                confidence=0.9,
                success=True,
            )
            sess.add(d)
            sess.commit()
            assert d.id is not None


class TestTask:
    def test_create_task(self):
        with Session() as sess:
            t = Task(task_type="scrape", status="running")
            sess.add(t)
            sess.commit()
            assert t.id is not None


class TestFailFastEnvValidation:
    """Fail-fast validation: production-mode missing keys → RuntimeError."""

    def test_raises_when_stripe_missing(self):
        """PostgreSQL-like URL + missing STRIPE_API_KEY → RuntimeError."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://user:pass@host/db",
            "STRIPE_API_KEY": "",
            "SENDGRID_API_KEY": "sg-real-key",
        }, clear=False):
            from src.config import Settings
            with pytest.raises(RuntimeError, match="STRIPE_API_KEY"):
                Settings()

    def test_raises_when_sendgrid_missing(self):
        """PostgreSQL-like URL + missing SENDGRID_API_KEY → RuntimeError."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://user:pass@host/db",
            "STRIPE_API_KEY": "sk_live_abc",
            "SENDGRID_API_KEY": "",
        }, clear=False):
            from src.config import Settings
            with pytest.raises(RuntimeError, match="SENDGRID_API_KEY"):
                Settings()

    def test_raises_when_both_missing(self):
        """PostgreSQL-like URL + both missing → RuntimeError mentions both."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://user:pass@host/db",
            "STRIPE_API_KEY": "",
            "SENDGRID_API_KEY": "",
        }, clear=False):
            from src.config import Settings
            with pytest.raises(RuntimeError) as exc:
                Settings()
            msg = str(exc.value)
            assert "STRIPE_API_KEY" in msg
            assert "SENDGRID_API_KEY" in msg

    def test_skipped_for_sqlite(self):
        """SQLite URL should never trigger the validation even if keys missing."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///data/test.db",
            "STRIPE_API_KEY": "",
            "SENDGRID_API_KEY": "",
        }, clear=False):
            from src.config import Settings
            s = Settings()
            # SQLite + missing keys → no RuntimeError (only PostgreSQL triggers it)
            assert s.database_url == "sqlite:///data/test.db"

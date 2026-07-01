"""
Integration tests for the FastAPI web server using starlette.testclient.TestClient.

Uses a file-based SQLite so the request thread and test thread share the same DB.
"""

from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.db import Base, Lead, Session, Task


@pytest.fixture(autouse=True)
def _db_and_env():
    """Use a temp file SQLite (not :memory:) so TestClient thread sees the same DB."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    db_url = f"sqlite:///{db_path}"
    os.environ["DATABASE_URL"] = db_url
    os.environ["OPENAI_API_KEY"] = "sk-test-dummy"
    os.environ.pop("API_KEY", None)
    os.environ.pop("STRIPE_WEBHOOK_SECRET", None)
    os.environ.pop("STRIPE_API_KEY", None)

    from src import config
    config.settings.api_key = None
    config.settings.stripe_webhook_secret = None
    config.settings.stripe_api_key = None
    config.settings.database_url = db_url

    from src.db import reset_engine
    reset_engine(db_url)
    # Ensure tables exist
    from src.db import _engine
    Base.metadata.create_all(bind=_engine)

    yield

    Session.remove()
    # Clean up file
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def client():
    from src.web import app
    return TestClient(app)


def _seed_lead(**kw):
    data = {"source": "test", "company_name": "Acme Corp"}
    data.update(kw)
    with Session() as sess:
        sess.add(Lead(**data))
        sess.commit()
    Session.remove()


def _seed_task():
    with Session() as sess:
        t = Task(task_type="test", status="done", result_json=json.dumps({"ok": True}))
        sess.add(t)
        sess.commit()
        tid = t.id
    Session.remove()
    return tid


class TestPublicRoutes:
    def test_landing_page(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestAuthGuardOff:
    def test_get_decisions(self, client):
        resp = client.get("/api/decisions")
        assert resp.status_code == 200
        assert "events" in resp.json()

    def test_get_leads(self, client):
        _seed_lead()
        resp = client.get("/api/leads")
        assert resp.status_code == 200
        data = resp.json()
        assert "leads" in data

    def test_get_tasks(self, client):
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        assert "tasks" in resp.json()

    def test_get_task_by_id_200(self, client):
        tid = _seed_task()
        resp = client.get(f"/api/tasks/{tid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == tid

    def test_get_task_by_id_404(self, client):
        resp = client.get("/api/tasks/99999")
        assert resp.status_code == 404

    def test_get_stats(self, client):
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        assert "total_leads" in resp.json()

    def test_get_subscription(self, client):
        resp = client.get("/api/subscription")
        assert resp.status_code == 200
        assert resp.json()["active"] is False

    def test_dashboard(self, client):
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_subscribe_demo_mode_without_stripe_key(self, client):
        resp = client.get("/api/subscribe")
        assert resp.status_code == 200
        assert resp.json() == {"url": "/onboarding?demo=true"}

    def test_scrape_missing_query(self, client):
        resp = client.post("/api/scrape", json={})
        assert resp.status_code == 400

    def test_scrape_empty_query(self, client):
        resp = client.post("/api/scrape", json={"query": ""})
        assert resp.status_code == 400

    def test_scrape_returns_task_id(self, client):
        resp = client.post("/api/scrape", json={"query": "test query", "limit": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert data["status"] == "running"
        assert isinstance(data["task_id"], int)

    def test_outreach_returns_task_id(self, client):
        resp = client.post("/api/outreach")
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert isinstance(data["task_id"], int)

    def test_task_polling(self, client):
        tid = _seed_task()
        resp = client.get(f"/api/tasks/{tid}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"


class TestAuthGuardOn:
    def test_all_reject_without_auth(self, client):
        from src import config
        config.settings.api_key = "test-key-123"
        try:
            for path in ["/api/decisions", "/api/leads", "/api/tasks", "/api/stats", "/api/subscription"]:
                resp = client.get(path)
                assert resp.status_code == 401, f"{path} should 401"
            resp = client.post("/api/scrape", json={"query": "x"})
            assert resp.status_code == 401
            resp = client.post("/api/outreach")
            assert resp.status_code == 401
            resp = client.get("/dashboard")
            assert resp.status_code == 401
        finally:
            config.settings.api_key = None

    def test_decisions_with_auth(self, client):
        from src import config
        config.settings.api_key = "test-key-123"
        try:
            resp = client.get("/api/decisions", headers={"Authorization": "Bearer test-key-123"})
            assert resp.status_code == 200
        finally:
            config.settings.api_key = None

    def test_dashboard_with_cookie(self, client):
        from src import config
        config.settings.api_key = "test-key-123"
        try:
            resp = client.get("/dashboard", cookies={"token": "test-key-123"})
            assert resp.status_code == 200
        finally:
            config.settings.api_key = None


class TestStripeWebhook:
    def test_rejects_without_secret(self, client):
        resp = client.post("/webhook", json={"type": "test"})
        assert resp.status_code == 503

    @patch("stripe.Webhook.construct_event")
    def test_accepts_valid(self, mock_construct, client):
        from src import config
        config.settings.stripe_webhook_secret = "whsec_test"
        try:
            mock_construct.return_value = {
                "type": "checkout.session.completed",
                "data": {"object": {"customer": "cus_1", "subscription": "sub_1",
                                     "customer_details": {"email": "a@b.com"}}},
            }
            resp = client.post("/webhook", json={}, headers={"stripe-signature": "sig"})
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"
        finally:
            config.settings.stripe_webhook_secret = None

    @patch("stripe.Webhook.construct_event")
    def test_rejects_bad_signature(self, mock_construct, client):
        from src import config
        from stripe.error import SignatureVerificationError
        config.settings.stripe_webhook_secret = "whsec_test"
        try:
            mock_construct.side_effect = SignatureVerificationError("bad", "{}")
            resp = client.post("/webhook", json={}, headers={"stripe-signature": "bad"})
            assert resp.status_code == 400
        finally:
            config.settings.stripe_webhook_secret = None


class TestTrackingWebhook:
    def test_delivered(self, client):
        _seed_lead(outreach_email_id="sg-msg-1")
        resp = client.post("/api/track", json=[{"event": "delivered", "sg_message_id": "sg-msg-1"}])
        assert resp.status_code == 200

    def test_open(self, client):
        _seed_lead(outreach_email_id="sg-msg-2")
        resp = client.post("/api/track", json=[{"event": "open", "sg_message_id": "sg-msg-2"}])
        assert resp.status_code == 200

    def test_bounce(self, client):
        _seed_lead(outreach_email_id="sg-msg-3")
        resp = client.post("/api/track", json=[{"event": "bounce", "sg_message_id": "sg-msg-3"}])
        assert resp.status_code == 200

    def test_unknown_message_id(self, client):
        resp = client.post("/api/track", json=[{"event": "open", "sg_message_id": "does-not-exist"}])
        assert resp.status_code == 200

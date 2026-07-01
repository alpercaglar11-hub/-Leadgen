"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


def _setup_memory_db():
    import os
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["OPENAI_API_KEY"] = "sk-test-dummy"
    from src.db import reset_engine, init_db
    reset_engine("sqlite:///:memory:")
    init_db()


@pytest.fixture(autouse=True)
def _test_db(monkeypatch):
    """Use in-memory SQLite. Priority given to test_routes which manages its own DB."""
    import os
    if os.environ.get("DATABASE_URL", "").startswith("sqlite:///") and not os.environ.get("DATABASE_URL").endswith(":memory:"):
        return
    _setup_memory_db()

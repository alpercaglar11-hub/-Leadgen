"""Database models, engine, session."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Index, Integer, String, Text,
    BigInteger, create_engine, func, select,
)
from sqlalchemy.orm import (
    Mapped, declarative_base, mapped_column, relationship, scoped_session, sessionmaker,
)

from src.config import settings

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
Base = declarative_base()


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    outreach_stage: Mapped[str] = mapped_column(
        String(32), nullable=False, default="new"
    )
    outreach_email_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LeadList(Base):
    __tablename__ = "lead_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    total_found: Mapped[int] = mapped_column(default=0)
    total_scraped: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    success: Mapped[bool | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    __table_args__ = (
        Index("ix_decision_logs_type_created", "decision_type", "created_at"),
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", index=True
    )
    params_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    lead_list_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("lead_lists.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Subscription(Base):
    """Stripe subscription — billing record."""
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stripe_customer_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    stripe_subscription_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


# ── Engine & session (lazy — tests call reset_engine before first use) ─
_engine = None
_registry: scoped_session | None = None


def _build_engine(url: str | None = None) -> None:
    global _engine, _registry
    url = url or settings.database_url or "sqlite:///data/leadgen.db"
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    _engine = create_engine(
        url,
        pool_pre_ping=True,
        connect_args=connect_args,
    )
    _registry = scoped_session(
        sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    )


def reset_engine(url: str | None = None) -> None:
    """Replace engine (for tests). Call before any Session() usage."""
    global _engine, _registry
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _registry = None
    _build_engine(url)


class SessionProxy:
    """Delegates to scoped_session; tests can swap the engine."""

    def __call__(self, **kw):
        if _registry is None:
            _build_engine()
        return _registry(**kw)

    def __enter__(self):
        if _registry is None:
            _build_engine()
        return _registry.__enter__()

    def __exit__(self, *a):
        if _registry is not None:
            return _registry.__exit__(*a)

    def remove(self):
        if _registry is not None:
            _registry.remove()

    def configure(self, **kw):
        if _registry is not None:
            _registry.configure(**kw)


Session = SessionProxy()


def init_db() -> None:
    if _engine is None:
        _build_engine()
    Base.metadata.create_all(bind=_engine)


def drop_db() -> None:
    if _engine is not None:
        Base.metadata.drop_all(bind=_engine)

"""initial schema — create all 5 tables

This is a *replacement* for the previous revision which only added columns
to a table that didn't exist.  On a fresh PostgreSQL database `alembic
upgrade head` must create every table before the web server starts.

Revision ID: bbfcd6c97ab2
Revises:
Create Date: 2026-06-27 12:35:08.296790

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "bbfcd6c97ab2"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _now() -> sa.TextClause:
    """Timezone-aware now() — works on PostgreSQL."""
    return sa.text("now()")


def upgrade() -> None:
    # ── leads ──────────────────────────────────────────────────────────
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source", sa.String(64), nullable=False, index=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("website", sa.String(512), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("address", sa.String(512), nullable=True),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("raw_data", sa.Text(), nullable=True),
        sa.Column(
            "outreach_stage", sa.String(32), nullable=False, server_default="new"
        ),
        sa.Column("outreach_email_id", sa.String(128), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=_now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=_now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── lead_lists ─────────────────────────────────────────────────────
    op.create_table(
        "lead_lists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("query", sa.String(255), nullable=False),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("total_found", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_scraped", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=_now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── decision_logs ──────────────────────────────────────────────────
    op.create_table(
        "decision_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("decision_type", sa.String(32), nullable=False, index=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("error_message", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=_now(),
            nullable=False,
            index=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_decision_logs_type_created",
        "decision_logs",
        ["decision_type", "created_at"],
    )

    # ── tasks ──────────────────────────────────────────────────────────
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_type", sa.String(64), nullable=False, index=True),
        sa.Column(
            "status",
            sa.String(32),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        sa.Column("params_json", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.String(512), nullable=True),
        sa.Column("lead_list_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=_now(),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── subscriptions ──────────────────────────────────────────────────
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "stripe_customer_id", sa.String(64), nullable=False, index=True
        ),
        sa.Column(
            "stripe_subscription_id", sa.String(64), nullable=False, unique=True
        ),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=_now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=_now(),
            nullable=False,
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("tasks")
    op.drop_index("ix_decision_logs_type_created", table_name="decision_logs")
    op.drop_table("decision_logs")
    op.drop_table("lead_lists")
    op.drop_table("leads")

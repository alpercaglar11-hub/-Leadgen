"""
Real-time event streaming engine for the live dashboard.

Architecture
------------
The orchestrator (sync, possibly in a different process or thread) writes
every decision to the ``decision_logs`` table.  The web server
(FastAPI, async) polls that table every ~500 ms and pushes new rows to
every connected WebSocket client as JSON.

This is deliberately **cross-process** — the cron agent and web server
can be in separate containers, and the live dashboard still works.

Usage (web server)::

    from src.stream import StreamManager

    manager = StreamManager()
    # Start the background poller on startup:
    await manager.start()
    # Accept a WebSocket:
    await manager.connect(websocket)
    # ... and when done:
    await manager.disconnect(websocket)
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import structlog
from fastapi import WebSocket

from src.db import DecisionLog, Session

logger = structlog.get_logger(__name__)

POLL_INTERVAL_S = 1.0
"""How often the background task polls the DB for new decisions."""

MAX_HISTORY_EVENTS = 50
"""How many historical decisions to send when a new client connects."""

HEARTBEAT_INTERVAL_S = 25.0
"""How often the server sends a keepalive ping to connected clients."""


class StreamManager:
    """Manages WebSocket connections and broadcasts new decisions.

    Usage::

        manager = StreamManager()
        await manager.start()           # begins polling
        await manager.connect(ws)       # registers client
        await manager.disconnect(ws)    # unregisters client
        await manager.stop()            # stops polling
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._last_id: int = 0
        self._poll_task: asyncio.Task | None = None
        self._hb_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        self._started = False

    # ── lifecycle ────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the background DB poller (idempotent)."""
        if self._started:
            return
        self._started = True
        # Seed last_id from the latest row in the DB
        try:
            self._last_id = self._get_max_decision_id()
        except Exception as exc:
            logger.warning("StreamManager could not read decision_logs: %s", exc)
            self._last_id = 0
        self._poll_task = asyncio.create_task(self._poll_loop())
        self._hb_task = asyncio.create_task(self._heartbeat_loop())
        logger.info(
            "StreamManager started: polling from decision_logs id=%d",
            self._last_id,
        )

    async def stop(self) -> None:
        """Stop the background poller."""
        for task in (self._poll_task, self._hb_task):
            if task is not None:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._poll_task = None
        self._hb_task = None
        self._started = False
        logger.info("StreamManager stopped")

    # ── connection management ────────────────────────────────────────

    async def connect(self, ws: WebSocket) -> None:
        """Accept a WebSocket and send backlog, then keep it open.

        This method is **safe** — if the DB query for history fails,
        the connection is still accepted and will receive live events
        as they come in.
        """
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)

        # Send historical decisions on connect — errors are non-fatal
        try:
            history = self._get_recent_decisions(limit=MAX_HISTORY_EVENTS)
            if history:
                await ws.send_text(json.dumps({
                    "type": "history",
                    "events": history,
                }))
        except Exception as exc:
            logger.warning("Could not send history to newly-connected WS: %s", exc)

        logger.debug("WebSocket connected (%d total)", len(self._connections))

    async def disconnect(self, ws: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self._connections.discard(ws)
        logger.debug("WebSocket disconnected (%d remaining)", len(self._connections))

    # ── heartbeat ───────────────────────────────────────────────────

    async def _heartbeat_loop(self) -> None:
        """Send a keepalive ping to all connected clients.

        This prevents proxies, load balancers, and idle timeouts from
        dropping the WebSocket.
        """
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL_S)
                payload = json.dumps({"type": "ping"})
                async with self._lock:
                    dead: list[WebSocket] = []
                    for ws in self._connections:
                        try:
                            await ws.send_text(payload)
                        except Exception:
                            dead.append(ws)
                    for ws in dead:
                        self._connections.discard(ws)
                if dead:
                    logger.debug("Heartbeat cleaned %d dead connection(s)", len(dead))
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Heartbeat loop crashed — will not restart")

    # ── polling ──────────────────────────────────────────────────────

    async def _poll_loop(self) -> None:
        """Background loop: poll DB for new decisions and broadcast."""
        try:
            while True:
                try:
                    new_events = self._fetch_new_decisions()
                    if new_events:
                        payload = json.dumps({
                            "type": "events",
                            "events": new_events,
                        })
                        async with self._lock:
                            dead: list[WebSocket] = []
                            for ws in self._connections:
                                try:
                                    await ws.send_text(payload)
                                except Exception:
                                    dead.append(ws)
                            for ws in dead:
                                self._connections.discard(ws)
                except Exception as exc:
                    logger.warning("Poll iteration failed: %s — continuing", exc)

                await asyncio.sleep(POLL_INTERVAL_S)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Stream poll loop crashed — will not restart")
            # Do NOT respawn — the user can reload the page and the next
            # stream_manager.start() call will create a fresh loop.

    # ── DB access (sync) ─────────────────────────────────────────────

    def _get_max_decision_id(self) -> int:
        try:
            with Session() as sess:
                row = sess.execute(
                    DecisionLog.__table__.select()
                    .order_by(DecisionLog.id.desc())
                    .limit(1)
                ).first()
                return row.id if row else 0
        finally:
            Session.remove()

    def _fetch_new_decisions(self) -> list[dict]:
        """Fetch all decisions with id > self._last_id."""
        try:
            with Session() as sess:
                rows = (
                    sess.execute(
                        DecisionLog.__table__.select()
                        .where(DecisionLog.id > self._last_id)
                        .order_by(DecisionLog.id.asc())
                    )
                    .all()
                )
                if not rows:
                    return []
                events = [_row_to_event(r) for r in rows]
                self._last_id = rows[-1].id
                return events
        finally:
            Session.remove()

    def _get_recent_decisions(self, limit: int = 50) -> list[dict]:
        """Fetch most recent decisions (for backfill on connect)."""
        try:
            with Session() as sess:
                rows = (
                    sess.execute(
                        DecisionLog.__table__.select()
                        .order_by(DecisionLog.id.desc())
                        .limit(limit)
                    )
                    .all()
                )
                return [_row_to_event(r) for r in reversed(rows)]
        finally:
            Session.remove()


# ── Decision logging (called from sync code, not async) ─────────────


def log_decision(
    sess,
    *,
    decision_type: str,
    reasoning: str | None = None,
    confidence: float | None = None,
    payload: dict | None = None,
    success: bool | None = None,
    error_message: str | None = None,
) -> int:
    """Record an agent decision in the database.

    *sess* is a SQLAlchemy session (required). The caller owns the
    transaction — call ``sess.commit()`` after this.

    The web server's ``StreamManager`` picks up new rows via polling
    and pushes them to browser clients.

    Returns the new ``DecisionLog.id``.
    """
    log = DecisionLog(
        decision_type=decision_type,
        reasoning=reasoning,
        confidence=confidence,
        payload_json=json.dumps(payload) if payload else None,
        success=success,
        error_message=error_message,
    )
    sess.add(log)
    sess.flush()
    logger.debug(
        "Decision logged: id=%d type=%s success=%s",
        log.id,
        decision_type,
        success,
    )
    return log.id


def _row_to_event(row) -> dict:
    """Convert a raw DecisionLog row to a JSON-serialisable dict."""
    return {
        "id": row.id,
        "type": row.decision_type,
        "reasoning": row.reasoning,
        "confidence": row.confidence,
        "payload": json.loads(row.payload_json) if row.payload_json else None,
        "success": row.success,
        "error": row.error_message,
        "timestamp": (
            row.created_at.isoformat()
            if isinstance(row.created_at, datetime)
            else str(row.created_at)
        ),
    }

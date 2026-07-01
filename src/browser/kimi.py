"""Kimi WebBridge browser provider."""

from __future__ import annotations

import json
import os
import uuid

WS_URL: str = os.getenv("BROWSER_WS_URL", "ws://127.0.0.1:10086/ws")
WS_TIMEOUT: float = float(os.getenv("BROWSER_TIMEOUT", "30"))
CONNECT_TIMEOUT: float = float(os.getenv("BROWSER_CONNECT_TIMEOUT", "5"))


class BrowserError(Exception):
    """Browser operation failed."""


class KimiBrowser:
    """Control Chrome via Kimi WebBridge WebSocket protocol."""

    def __init__(self, ws_url: str = WS_URL) -> None:
        self._ws_url = ws_url
        self._ws_sync = None
        try:
            import websockets.sync.client as ws_sync
            self._ws_sync = ws_sync
        except ImportError:
            pass

    def check_available(self) -> bool:
        if self._ws_sync is None:
            return False
        try:
            with self._ws_sync.connect(self._ws_url, timeout=CONNECT_TIMEOUT) as ws:
                ws.send(json.dumps({"type": "ping"}))
            return True
        except (ConnectionRefusedError, OSError, TimeoutError):
            return False

    def call(self, action: str, args: dict | None = None) -> dict:
        if self._ws_sync is None:
            raise BrowserError("websockets library not available; pip install websockets")
        payload = {
            "type": "tool_call",
            "requestId": str(uuid.uuid4()),
            "payload": {"name": action, "args": args or {}},
        }
        try:
            with self._ws_sync.connect(self._ws_url, timeout=CONNECT_TIMEOUT) as ws:
                ws.send(json.dumps(payload))
                raw = ws.recv(timeout=WS_TIMEOUT)
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                msg = json.loads(raw)
        except (ConnectionRefusedError, OSError) as exc:
            raise BrowserError(f"Cannot connect to Kimi WebBridge: {exc}") from exc
        except TimeoutError as exc:
            raise BrowserError(f"Request timed out after {WS_TIMEOUT}s") from exc
        except Exception as exc:
            raise BrowserError(f"WebSocket error: {exc}") from exc
        if msg.get("type") == "tool_result":
            err = msg.get("payload", {}).get("error")
            if err:
                raise BrowserError(err)
            return msg["payload"].get("data", {})
        raise BrowserError(f"Unexpected message: {msg.get('type')}")

    def navigate(self, url: str) -> dict:
        return self.call("navigate", {"url": url})

    def snapshot(self) -> dict:
        return self.call("snapshot")

    def click(self, selector: str) -> dict:
        return self.call("click", {"selector": selector})

    def fill(self, selector: str, value: str) -> dict:
        return self.call("fill", {"selector": selector, "value": value})

    def screenshot(self) -> dict:
        return self.call("screenshot")

    def evaluate(self, js: str) -> dict:
        return self.call("evaluate", {"code": js})

    def list_tabs(self) -> dict:
        return self.call("list_tabs")

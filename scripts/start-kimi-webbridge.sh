#!/bin/bash
# ────────────────────────────────────────────────────────────────
# Kimi WebBridge — Browser Automation Service Launcher
# ────────────────────────────────────────────────────────────────
# Starts:
#   1. The Kimi WebBridge MCP server (WebSocket on port 10086)
#   2. Chrome with remote debugging (CDP on port 9222)
#
# Architecture:
#   Claude Code → MCP stdio → WebSocket :10086 ↔ Chrome Extension ↔ CDP → Browser
#
# Prerequisites:
#   - Kimi WebBridge Chrome extension installed
#     (https://chromewebstore.google.com/detail/kimi-webbridge/fldmhceldgbpfpkbgopacenieobmligc)
#   - Node.js >= 18
# ────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
CHROME_EXE="/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
CDP_PORT=9222
WS_PORT=10086
USER_DATA_DIR="$HOME/.kimi-webbridge-chrome-data"
WS_URL="ws://127.0.0.1:${WS_PORT}/ws"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cleanup() {
    echo -e "\n${YELLOW}Shutting down Kimi WebBridge services...${NC}"
    # Kill Chrome remote debugging instance
    if [ -n "${CHROME_PID:-}" ]; then
        kill "$CHROME_PID" 2>/dev/null || true
    fi
    # Kill MCP server
    if [ -n "${MCP_PID:-}" ]; then
        kill "$MCP_PID" 2>/dev/null || true
    fi
    echo -e "${GREEN}Done.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "╔══════════════════════════════════════════════════════╗"
echo "║     Kimi WebBridge Service Launcher                  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Check Chrome exists ──────────────────────────────
if [ -f "$CHROME_EXE" ]; then
    echo -e "${GREEN}✓${NC} Chrome found: $CHROME_EXE"
else
    echo -e "${RED}✗${NC} Chrome not found at $CHROME_EXE"
    echo "  Please install Chrome or update CHROME_EXE in this script."
    exit 1
fi

# ── Step 2: Create user data dir if needed ───────────────────
mkdir -p "$USER_DATA_DIR"

# ── Step 3: Check port availability ───────────────────────────
if ss -tlnp 2>/dev/null | grep -q ":${CDP_PORT} "; then
    echo -e "${YELLOW}⚠${NC} Port $CDP_PORT is already in use (Chrome may be running)"
    echo "  Using existing Chrome instance."
else
    echo -e "${GREEN}✓${NC} Starting Chrome with remote debugging on port $CDP_PORT..."
    # Start Chrome from WSL
    powershell.exe -Command "Start-Process -WindowStyle Hidden '$CHROME_EXE' -ArgumentList '--remote-debugging-port=$CDP_PORT --user-data-dir=C:\\Users\\alper\\.kimi-webbridge-chrome-data --no-first-run --no-default-browser-check'"
    CHROME_PID=$!
    echo -e "${GREEN}✓${NC} Chrome starting with CDP on port $CDP_PORT"
    sleep 3
fi

# ── Step 4: Start the MCP server in background ────────────────
echo -e "${GREEN}✓${NC} Starting Kimi WebBridge MCP server..."
kimi-webbridge mcp &
MCP_PID=$!

# ── Step 5: Wait for WebSocket server ──────────────────────────
echo -n "  Waiting for WebSocket server on port $WS_PORT..."
for i in $(seq 1 15); do
    if ss -tlnp 2>/dev/null | grep -q ":${WS_PORT} "; then
        echo -e " ${GREEN}ready!${NC}"
        break
    fi
    sleep 1
    echo -n "."
done

if ! ss -tlnp 2>/dev/null | grep -q ":${WS_PORT} "; then
    echo -e "\n${RED}✗${NC} WebSocket server did not start."
    cleanup
    exit 1
fi

# ── Step 6: Open Chrome Web Store for extension ───────────────
EXTENSION_ID="fldmhceldgbpfpkbgopacenieobmligc"
echo ""
echo -e "${YELLOW}📌 IMPORTANT:${NC} If you haven't already, install the Kimi WebBridge"
echo "   Chrome extension from:"
echo "   https://chromewebstore.google.com/detail/kimi-webbridge/${EXTENSION_ID}"
echo ""
echo -e "${GREEN}✓${NC} All services running!"
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Service           Endpoint                         ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  MCP Server        stdio (via claude.json config)   ║"
echo "║  WebSocket         ws://127.0.0.1:${WS_PORT}/ws         ║"
echo "║  Chrome CDP        http://127.0.0.1:${CDP_PORT}          ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  Press Ctrl+C to stop all services."
echo ""

# Wait for signals
wait

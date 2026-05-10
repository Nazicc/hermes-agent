#!/usr/bin/env python3
"""
browser-harness MCP Server

Exposes browser-harness browser control capabilities as MCP tools.
The daemon auto-starts on first tool call (via ensure_daemon).

Architecture:
  Hermes Agent → MCP Client → bh_mcp.py (this server)
                                     │
                              browser-harness helpers
                              (CDP over Unix socket IPC)
                                     │
                              browser-harness daemon
                              (CDP WebSocket → Chrome)

Prerequisites:
  - Chrome must be running with --remote-debugging-port=9222
    (or set BU_CDP_URL/BU_CDP_WS env vars)
  - Or: Browser Use Cloud with BROWSER_USE_API_KEY

Usage:
  python bh_mcp.py

Environment (set via config.yaml):
  BH_AGENT_WORKSPACE  — path to agent-editable helpers + domain-skills
  BU_NAME             — daemon name (default: "hermes-agent")
  BU_CDP_URL          — http://host:port for CDP (if not using default Chrome profile)
  BU_CDP_WS           — explicit WebSocket URL (overrides BU_CDP_URL)
  BROWSER_USE_API_KEY — Browser Use Cloud API key
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
import os
import sys
import threading
from pathlib import Path
from typing import Any

# ── Environment Setup ─────────────────────────────────────────────────────────
# Must be set BEFORE importing browser_harness modules.
_BH_ROOT = Path(__file__).parent / "browser_harness"
sys.path.insert(0, str(_BH_ROOT / "src"))

# Resolve workspace path (agent-editable helpers + domain-skills)
_MCP_DIR = Path(__file__).parent
_AGENT_WORKSPACE = os.environ.get(
    "BH_AGENT_WORKSPACE",
    str(_MCP_DIR.parent.parent.parent / "browser-harness-workspace"),
)
os.environ.setdefault("BH_AGENT_WORKSPACE", _AGENT_WORKSPACE)
os.environ.setdefault("BU_NAME", "hermes-agent-bh")

_CDP_URL = os.environ.get("BU_CDP_URL", "http://127.0.0.1:9222")
os.environ.setdefault("BU_CDP_URL", _CDP_URL)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [browser-harness-mcp] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ── MCP Server ────────────────────────────────────────────────────────────────
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

APP_NAME = "browser-harness"
APP_VERSION = "0.1.0"
server = Server(APP_NAME)

# ── Lazy Import & Daemon Init ─────────────────────────────────────────────────
# Thread pool for blocking helper calls
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
_daemon_ready = threading.Event()
_import_error: str | None = None

# Deferred so env vars above are set first
def _ensure_harness():
    global _import_error
    if _import_error == "blocked":
        return None, None, None
    try:
        # Import admin first — ensure_daemon starts the daemon before helpers are used
        from browser_harness import admin as bh_admin
        from browser_harness import helpers as bh_helpers
        from browser_harness import _ipc as bh_ipc
        return bh_helpers, bh_admin, bh_ipc
    except Exception as e:
        _import_error = str(e)
        logger.error(f"Failed to import browser_harness: {e}")
        return None, None, None


def _run_in_thread(fn, *args, **kwargs):
    """Execute a blocking function in the thread pool."""
    future = _executor.submit(fn, *args, **kwargs)
    return future.result(timeout=60)


def _daemon_init():
    """Called once on first tool call to start the daemon."""
    global _daemon_ready
    if _daemon_ready.is_set():
        return True
    helpers, admin, _ = _ensure_harness()
    if helpers is None:
        return False
    try:
        # ensure_daemon is blocking; run in thread pool
        _run_in_thread(admin.ensure_daemon, wait=60.0)
        _daemon_ready.set()
        logger.info("Daemon started and ready")
        return True
    except Exception as e:
        logger.error(f"Daemon start failed: {e}")
        return False


# ── Tool Definitions ─────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # ── Navigation ────────────────────────────────────────────────
        Tool(
            name="bh_goto_url",
            description=(
                "Navigate browser to a URL. Returns CDP frameId/loaderId. "
                "Use bh_wait_for_load() after this to wait for page load."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to navigate to (https://... or http://...)",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="bh_page_info",
            description=(
                "Get current page state: url, title, window size, scroll position, "
                "dialog status. Call this after navigation or any action to verify state."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        # ── Input ────────────────────────────────────────────────────
        Tool(
            name="bh_click_at_xy",
            description=(
                "Click at screen coordinates. Preferred over DOM selectors — "
                "works through iframes, shadow DOM, and cross-origin frames "
                "because it dispatches at the Chrome compositor level. "
                "Use bh_capture_screenshot first to get coordinates, then verify with another screenshot."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "number", "description": "X coordinate in CSS pixels"},
                    "y": {"type": "number", "description": "Y coordinate in CSS pixels"},
                    "button": {
                        "type": "string",
                        "enum": ["left", "right", "middle"],
                        "default": "left",
                    },
                    "clicks": {"type": "integer", "default": 1},
                },
                "required": ["x", "y"],
            },
        ),
        Tool(
            name="bh_fill_input",
            description=(
                "Fill a form input field (text input, textarea) identified by CSS selector. "
                "Triggers React/Vue/Ember framework events. Use bh_type_text for plain text without events."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector (e.g. '#search', 'input[name=q]')"},
                    "text": {"type": "string", "description": "Text to type into the field"},
                    "clear_first": {"type": "boolean", "default": True},
                },
                "required": ["selector", "text"],
            },
        ),
        Tool(
            name="bh_type_text",
            description=(
                "Type raw text as keyboard input events. Bypasses framework event listeners. "
                "Use bh_fill_input for normal form filling with framework events."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="bh_press_key",
            description="Press a keyboard key (Enter, Escape, Tab, Backspace, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key name (Enter, Escape, Tab, ArrowDown, etc.)"},
                    "modifiers": {"type": "integer", "default": 0, "description": "Bitmask: 1=Shift, 2=Ctrl, 4=Alt"},
                },
                "required": ["key"],
            },
        ),
        Tool(
            name="bh_scroll",
            description="Scroll the current page. dx/dy are pixel deltas (negative = up/left).",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "number", "default": 0, "description": "Target X (or delta if relative)"},
                    "y": {"type": "number", "default": -300, "description": "Target Y or delta (negative = scroll up)"},
                    "dy": {"type": "number", "default": -300},
                    "dx": {"type": "number", "default": 0},
                },
            },
        ),
        # ── Screenshot / Visual ───────────────────────────────────────
        Tool(
            name="bh_capture_screenshot",
            description=(
                "Capture a screenshot of the current page. "
                "Returns the file path. "
                "Use coordinates from the screenshot to drive bh_click_at_xy. "
                "Screenshot-first workflow: capture → read pixels → click → capture again to verify."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Output file path (default: /tmp/bh_screenshot.png)"},
                    "full": {"type": "boolean", "default": False, "description": "Capture full scrollable page"},
                    "max_dim": {"type": "number", "description": "Max dimension in pixels (downscaling)"},
                },
            },
        ),
        # ── Wait / Poll ───────────────────────────────────────────────
        Tool(
            name="bh_wait",
            description="Wait for N seconds (for page transitions, animations).",
            inputSchema={
                "type": "object",
                "properties": {
                    "seconds": {"type": "number", "default": 1.0},
                },
            },
        ),
        Tool(
            name="bh_wait_for_load",
            description="Wait for the current page to finish loading (network idle + DOM ready).",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeout": {"type": "number", "default": 15.0},
                },
            },
        ),
        Tool(
            name="bh_wait_for_element",
            description=(
                "Wait for a DOM element matching the CSS selector to appear. "
                "Polls the DOM every 0.5s. Returns element info once found. "
                "Best for SPAs where networkidle doesn't mean 'content ready'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "timeout": {"type": "number", "default": 10.0},
                    "visible": {"type": "boolean", "default": False, "description": "Wait until element is visible (not hidden)"},
                },
                "required": ["selector"],
            },
        ),
        Tool(
            name="bh_wait_for_network_idle",
            description="Wait for all network requests to settle (form submissions, API calls).",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeout": {"type": "number", "default": 10.0},
                    "idle_ms": {"type": "number", "default": 500},
                },
            },
        ),
        # ── Tab Management ────────────────────────────────────────────
        Tool(
            name="bh_list_tabs",
            description="List all open browser tabs. Returns list of {targetId, url, title, type}.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="bh_switch_tab",
            description="Switch to a different tab by target ID (from bh_list_tabs).",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Tab target ID or 'next'/'prev'"},
                },
                "required": ["target"],
            },
        ),
        Tool(
            name="bh_new_tab",
            description="Open a new tab. Returns the new tab's target ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "default": "about:blank"},
                },
            },
        ),
        # ── JavaScript ────────────────────────────────────────────────
        Tool(
            name="bh_js",
            description=(
                "Execute arbitrary JavaScript in the current page context. "
                "Can return a value if the JS expression returns something. "
                "Use for: reading page state, triggering custom logic, extracting data."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "JavaScript expression or statement"},
                },
                "required": ["expression"],
            },
        ),
        # ── HTTP (no browser) ─────────────────────────────────────────
        Tool(
            name="bh_http_get",
            description=(
                "Make an HTTP GET request without launching a browser. "
                "Respects BH_AGENT_WORKSPACE .env proxy settings. "
                "Use for: API calls, fetching raw pages when browser is not needed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "headers": {"type": "object"},
                    "timeout": {"type": "number", "default": 20.0},
                },
                "required": ["url"],
            },
        ),
        # ── Admin / Diagnostics ────────────────────────────────────────
        Tool(
            name="bh_doctor",
            description=(
                "Run browser-harness diagnostics: checks Chrome connectivity, daemon status, "
                "install mode, and whether a newer version is available. "
                "Run this when tools are failing to diagnose the issue."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="bh_browser_connections",
            description="List all active browser-harness daemon connections (local + cloud).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="bh_ensure_daemon",
            description=(
                "Ensure the browser-harness daemon is running. "
                "Starts it if not running, or verifies liveness if already running. "
                "Normally auto-called on first tool use; explicit call useful after Chrome restart."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "wait": {"type": "number", "default": 60.0},
                },
            },
        ),
        Tool(
            name="bh_restart_daemon",
            description="Stop and restart the browser-harness daemon. Use after Chrome restart.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="bh_drain_events",
            description="Drain and return all captured CDP events since last call (Page, DOM, Network events).",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


# ── Tool Handler ─────────────────────────────────────────────────────────────

def _safe_helper_call(fn, *args, **kwargs):
    """Call a browser-harness helper with error translation."""
    try:
        result = fn(*args, **kwargs)
        return result
    except RuntimeError as e:
        raise RuntimeError(f"browser-harness error: {e}")
    except Exception as e:
        raise RuntimeError(f"{type(e).__name__}: {e}")


def _call_sync(name: str, arguments: dict[str, Any]) -> str:
    """Synchronous tool implementation. Runs in thread pool."""
    # Ensure daemon on first call
    _daemon_init()

    helpers, admin, _ = _ensure_harness()
    if helpers is None:
        raise RuntimeError(f"browser-harness not available: {_import_error}")

    # ── Navigation ──────────────────────────────────────────────────
    if name == "bh_goto_url":
        r = _safe_helper_call(helpers.goto_url, arguments["url"])
        return json.dumps({"result": r}, default=str)

    if name == "bh_page_info":
        r = _safe_helper_call(helpers.page_info)
        return json.dumps({"page": r}, default=str)

    # ── Input ───────────────────────────────────────────────────────
    if name == "bh_click_at_xy":
        r = _safe_helper_call(
            helpers.click_at_xy,
            arguments["x"],
            arguments["y"],
            arguments.get("button", "left"),
            arguments.get("clicks", 1),
        )
        return json.dumps({"result": r}, default=str)

    if name == "bh_fill_input":
        r = _safe_helper_call(
            helpers.fill_input,
            arguments["selector"],
            arguments["text"],
            arguments.get("clear_first", True),
        )
        return json.dumps({"result": r}, default=str)

    if name == "bh_type_text":
        _safe_helper_call(helpers.type_text, arguments["text"])
        return json.dumps({"ok": True})

    if name == "bh_press_key":
        _safe_helper_call(
            helpers.press_key,
            arguments["key"],
            arguments.get("modifiers", 0),
        )
        return json.dumps({"ok": True})

    if name == "bh_scroll":
        _safe_helper_call(
            helpers.scroll,
            arguments.get("x", 0),
            arguments.get("y", -300),
            arguments.get("dy", -300),
            arguments.get("dx", 0),
        )
        return json.dumps({"ok": True})

    # ── Screenshot ───────────────────────────────────────────────────
    if name == "bh_capture_screenshot":
        path = arguments.get("path") or "/tmp/bh_screenshot.png"
        r = _safe_helper_call(
            helpers.capture_screenshot,
            path=path,
            full=arguments.get("full", False),
            max_dim=arguments.get("max_dim"),
        )
        return json.dumps({"screenshot_path": str(r), "path": path}, default=str)

    # ── Wait ────────────────────────────────────────────────────────
    if name == "bh_wait":
        _safe_helper_call(helpers.wait, arguments.get("seconds", 1.0))
        return json.dumps({"ok": True})

    if name == "bh_wait_for_load":
        _safe_helper_call(helpers.wait_for_load, arguments.get("timeout", 15.0))
        return json.dumps({"ok": True})

    if name == "bh_wait_for_element":
        r = _safe_helper_call(
            helpers.wait_for_element,
            arguments["selector"],
            arguments.get("timeout", 10.0),
            arguments.get("visible", False),
        )
        return json.dumps({"result": r}, default=str)

    if name == "bh_wait_for_network_idle":
        _safe_helper_call(
            helpers.wait_for_network_idle,
            arguments.get("timeout", 10.0),
            arguments.get("idle_ms", 500),
        )
        return json.dumps({"ok": True})

    # ── Tabs ────────────────────────────────────────────────────────
    if name == "bh_list_tabs":
        r = _safe_helper_call(helpers.list_tabs)
        return json.dumps({"tabs": r}, default=str)

    if name == "bh_switch_tab":
        _safe_helper_call(helpers.switch_tab, arguments["target"])
        return json.dumps({"ok": True, "switched_to": arguments["target"]})

    if name == "bh_new_tab":
        r = _safe_helper_call(helpers.new_tab, arguments.get("url", "about:blank"))
        return json.dumps({"result": r}, default=str)

    # ── JavaScript ─────────────────────────────────────────────────
    if name == "bh_js":
        r = _safe_helper_call(helpers.js, arguments["expression"])
        return json.dumps({"result": r}, default=str)

    # ── HTTP ────────────────────────────────────────────────────────
    if name == "bh_http_get":
        r = _safe_helper_call(
            helpers.http_get,
            arguments["url"],
            arguments.get("headers"),
            arguments.get("timeout", 20.0),
        )
        return json.dumps({"result": r}, default=str)

    # ── Admin ──────────────────────────────────────────────────────
    if name == "bh_doctor":
        # run_doctor prints; capture stdout
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            admin.run_doctor()
        return json.dumps({"doctor_output": buf.getvalue()}, default=str)

    if name == "bh_browser_connections":
        r = admin.browser_connections()
        return json.dumps({"connections": r}, default=str)

    if name == "bh_ensure_daemon":
        _run_in_thread(admin.ensure_daemon, wait=arguments.get("wait", 60.0))
        return json.dumps({"ok": True, "daemon": "running"})

    if name == "bh_restart_daemon":
        _run_in_thread(admin.restart_daemon)
        _daemon_ready.clear()
        return json.dumps({"ok": True, "daemon": "restarting"})

    if name == "bh_drain_events":
        r = _safe_helper_call(helpers.drain_events)
        return json.dumps({"events": r}, default=str)

    return json.dumps({"error": f"Unknown tool: {name}"})


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(_executor, _call_sync, name, arguments)
        return [TextContent(type="text", text=result)]
    except RuntimeError as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, default=str))]
    except Exception as e:
        logger.exception(f"Error in {name}")
        return [TextContent(type="text", text=json.dumps({"error": f"{type(e).__name__}: {e}"}, default=str))]


# ── Main ─────────────────────────────────────────────────────────────────────

async def main():
    logger.info(f"browser-harness MCP Server starting (workspace: {_AGENT_WORKSPACE})")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())

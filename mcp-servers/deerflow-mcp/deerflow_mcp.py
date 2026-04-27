#!/usr/bin/env python3
"""
DeerFlow MCP Server — Exposes DeerFlow agent capabilities as MCP tools.

Architecture:
  Hermes Agent → MCP Client → deerflow_mcp.py (this server)
                                    ↓
                              DeerFlowClient
                                    ↓
                              Ollama / OpenAI / etc.

Usage:
  python deerflow_mcp.py

Environment:
  DEER_FLOW_CONFIG_PATH  — path to config.yaml (default: repo root)
  DEERFLOW_PYTHON_PATH   — path to Python with DeerFlow installed
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any

# Setup paths
SCRIPT_DIR = Path(__file__).parent
DEERFLOW_REPO = os.environ.get(
    "DEERFLOW_REPO",
    "/Users/can/.hermes/deer-flow-repo",
)
CONFIG_PATH = os.environ.get(
    "DEERFLOW_CONFIG_PATH",
    str(Path(DEERFLOW_REPO) / "config.yaml"),
)

# Prepend DeerFlow harness package to path
sys.path.insert(0, str(Path(DEERFLOW_REPO) / "backend" / "packages" / "harness"))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from deerflow.client import DeerFlowClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# App metadata
APP_NAME = "deerflow"
APP_VERSION = "1.0.0"

# Lazy-initialized client (created on first tool call)
_client: DeerFlowClient | None = None


def get_client() -> DeerFlowClient:
    """Get or create the DeerFlow client (lazy init)."""
    global _client
    if _client is None:
        logger.info(f"Initializing DeerFlowClient with config: {CONFIG_PATH}")
        if not Path(CONFIG_PATH).exists():
            raise FileNotFoundError(
                f"config.yaml not found at {CONFIG_PATH}. "
                "Run 'cd {DEERFLOW_REPO} && make config' first."
            )
        _client = DeerFlowClient(config_path=CONFIG_PATH)
        logger.info("DeerFlowClient initialized")
    return _client


# Build MCP server
server = Server(APP_NAME)


# ─── Tool Definitions ────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="deerflow_chat",
            description=(
                "Send a message to the DeerFlow research agent and get a response. "
                "Use this for: deep research, multi-step analysis, structured reports, "
                "web search + synthesis, document understanding. "
                "Supports long-running research tasks with sub-agents and tool use. "
                "Returns the full agent response as text."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The user's message or research task",
                    },
                    "thread_id": {
                        "type": "string",
                        "description": "Optional conversation thread ID for context continuity. "
                                      "If omitted, a random ID is generated.",
                    },
                    "thinking_enabled": {
                        "type": "boolean",
                        "description": "Enable extended thinking (CoT/reasoning). Default: true",
                        "default": True,
                    },
                    "model_name": {
                        "type": "string",
                        "description": "Optional model override from config.yaml",
                    },
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="deerflow_stream",
            description=(
                "Stream a DeerFlow conversation turn with real-time token deltas. "
                "Use for interactive research where you want to see the agent think. "
                "Yields structured events: AI text deltas, tool calls, tool results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The user's message",
                    },
                    "thread_id": {
                        "type": "string",
                        "description": "Optional thread ID",
                    },
                    "thinking_enabled": {
                        "type": "boolean",
                        "description": "Enable extended thinking. Default: true",
                        "default": True,
                    },
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="deerflow_list_models",
            description="List all models configured in DeerFlow config.yaml",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="deerflow_list_skills",
            description="List all skills (tools/extensions) available in DeerFlow",
            inputSchema={
                "type": "object",
                "properties": {
                    "enabled_only": {
                        "type": "boolean",
                        "description": "Only list enabled skills. Default: false",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="deerflow_health",
            description="Check DeerFlow client health and configuration status",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


# ─── Tool Handler ─────────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        client = get_client()

        if name == "deerflow_health":
            models = client.list_models()
            skills = client.list_skills()
            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "healthy",
                    "config_path": CONFIG_PATH,
                    "config_exists": Path(CONFIG_PATH).exists(),
                    "models_count": len(models.get("models", [])),
                    "skills_count": len(skills.get("skills", [])),
                    "version": APP_VERSION,
                }, indent=2),
            )]

        elif name == "deerflow_list_models":
            result = client.list_models()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "deerflow_list_skills":
            enabled_only = arguments.get("enabled_only", False)
            result = client.list_skills(enabled_only=enabled_only)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "deerflow_chat":
            message = arguments["message"]
            thread_id = arguments.get("thread_id") or f"hermes-{uuid.uuid4().hex[:8]}"
            thinking = arguments.get("thinking_enabled", True)
            model_name = arguments.get("model_name")

            logger.info(f"deerflow_chat thread={thread_id} thinking={thinking}")

            response = client.chat(
                message,
                thread_id=thread_id,
                thinking_enabled=thinking,
                model_name=model_name,
            )
            return [TextContent(type="text", text=response or "(no response)")]

        elif name == "deerflow_stream":
            message = arguments["message"]
            thread_id = arguments.get("thread_id") or f"hermes-{uuid.uuid4().hex[:8]}"
            thinking = arguments.get("thinking_enabled", True)

            logger.info(f"deerflow_stream thread={thread_id}")
            events = []
            for event in client.stream(message, thread_id=thread_id, thinking_enabled=thinking):
                events.append({"type": event.type, "data": event.data})
                # Stop after end event to avoid huge output
                if event.type == "end":
                    break
            return [TextContent(type="text", text=json.dumps(events, indent=2, ensure_ascii=False))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except FileNotFoundError as e:
        logger.error(f"Config not found: {e}")
        return [TextContent(type="text", text=f"Configuration error: {e}")]
    except Exception as e:
        logger.exception(f"Error in {name}")
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {e}")]


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    logger.info(f"DeerFlow MCP Server starting (config: {CONFIG_PATH})")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
DeepCode MCP Server — Exposes DeepCode capabilities as MCP tools.

Architecture:
  Hermes Agent → MCP Client → deepcode_mcp.py (this server)
                                    ↓
                              DeepCode REST API (:8000)

Usage:
  python deepcode_mcp.py

Environment:
  DEEPCODE_BASE_URL  — DeepCode API base URL (default: http://127.0.0.1:8000)
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
BASE_URL = os.environ.get("DEEPCODE_BASE_URL", "http://127.0.0.1:8000")

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

APP_NAME = "deepcode"
APP_VERSION = "1.0.0"

# Lazy HTTP client
_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(base_url=BASE_URL, timeout=120.0)
        logger.info(f"DeepCode client initialized against {BASE_URL}")
    return _client


server = Server(APP_NAME)


# ─── Tool Definitions ────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="deepcode_chat_planning",
            description=(
                "Submit a task to DeepCode's chat-planning workflow. Use this when you need "
                "DeepCode to plan, analyze requirements, or break down a coding task. "
                "Returns a task_id for tracking and further interaction."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The user's task description or question for DeepCode",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for context continuity. "
                                      "If omitted, a new session is created.",
                    },
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="deepcode_paper_to_code",
            description=(
                "Submit a paper URL or description to DeepCode's paper-to-code workflow. "
                "DeepCode will read the paper and generate corresponding code implementation. "
                "Returns a task_id for tracking."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "paper_url": {
                        "type": "string",
                        "description": "URL of the paper (e.g., arXiv link) to convert to code",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional natural language description of what to implement",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID",
                    },
                },
                "required": ["paper_url"],
            },
        ),
        Tool(
            name="deepcode_workflow_status",
            description="Get the status and result of a DeepCode workflow task by task_id.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The task ID returned from chat_planning or paper_to_code",
                    },
                },
                "required": ["task_id"],
            },
        ),
        Tool(
            name="deepcode_workflow_respond",
            description=(
                "Send a follow-up response to an active DeepCode workflow task. "
                "Use this to provide additional input or clarification after "
                "deepcode_workflow_status shows it needs more information."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The task ID from an active DeepCode workflow",
                    },
                    "message": {
                        "type": "string",
                        "description": "Your response or input to the workflow",
                    },
                },
                "required": ["task_id", "message"],
            },
        ),
        Tool(
            name="deepcode_requirements_questions",
            description=(
                "Send requirements text to DeepCode for analysis and question generation. "
                "DeepCode will analyze the requirements and ask clarifying questions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "requirements": {
                        "type": "string",
                        "description": "The requirements text or description to analyze",
                    },
                },
                "required": ["requirements"],
            },
        ),
        Tool(
            name="deepcode_requirements_summarize",
            description=(
                "Summarize a set of requirements into a concise description. "
                "DeepCode will distill key points and produce a clean summary."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "requirements": {
                        "type": "string",
                        "description": "The requirements text to summarize",
                    },
                },
                "required": ["requirements"],
            },
        ),
        Tool(
            name="deepcode_active_workflows",
            description="List currently active DeepCode workflow tasks.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="deepcode_recent_workflows",
            description="List recent DeepCode workflow tasks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max number of recent tasks to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        Tool(
            name="deepcode_health",
            description="Check DeepCode API health and connectivity.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


# ─── Tool Handler ─────────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        client = get_client()

        if name == "deepcode_health":
            resp = await client.get("/health")
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deepcode_active_workflows":
            resp = await client.get("/api/v1/workflows/active")
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deepcode_recent_workflows":
            limit = arguments.get("limit", 10)
            resp = await client.get("/api/v1/workflows/recent", params={"limit": limit})
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deepcode_chat_planning":
            payload = {
                "message": arguments["message"],
                "session_id": arguments.get("session_id") or f"hermes-{uuid.uuid4().hex[:8]}",
            }
            resp = await client.post("/api/v1/workflows/chat-planning", json=payload)
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deepcode_paper_to_code":
            payload = {
                "paper_url": arguments["paper_url"],
                "description": arguments.get("description", ""),
                "session_id": arguments.get("session_id") or f"hermes-{uuid.uuid4().hex[:8]}",
            }
            resp = await client.post("/api/v1/workflows/paper-to-code", json=payload)
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deepcode_workflow_status":
            task_id = arguments["task_id"]
            resp = await client.get(f"/api/v1/workflows/status/{task_id}")
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deepcode_workflow_respond":
            payload = {
                "message": arguments["message"],
            }
            task_id = arguments["task_id"]
            resp = await client.post(f"/api/v1/workflows/respond/{task_id}", json=payload)
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deepcode_requirements_questions":
            payload = {"requirements": arguments["requirements"]}
            resp = await client.post("/api/v1/requirements/questions", json=payload)
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deepcode_requirements_summarize":
            payload = {"requirements": arguments["requirements"]}
            resp = await client.post("/api/v1/requirements/summarize", json=payload)
            resp.raise_for_status()
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        return [TextContent(type="text", text=f"HTTP {e.response.status_code}: {e.response.text}")]
    except Exception as e:
        logger.exception(f"Error in {name}")
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {e}")]


# ─── Main ─────────────────────────────────────────────────────────────────────

async def main():
    logger.info(f"DeepCode MCP Server starting (base_url: {BASE_URL})")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

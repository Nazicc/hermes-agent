#!/usr/bin/env python3
"""
DeepTutor MCP Server — Exposes DeepTutor capabilities as MCP tools.

Architecture:
  Hermes Agent → MCP Client → deeptutor_mcp.py (this server)
                                    ↓
                              DeepTutor REST API (:8001)

Capabilities exposed:
  - Knowledge Base (RAG): upload docs, query, manage knowledge bases
  - TutorBot: create/query AI tutors with custom SOULs
  - Co-Writer: interactive learning-by-writing with AI feedback
  - Book: structured learning content with deep-dive and quiz
  - Notebook: Q&A note-taking
  - Question-Notebook: flashcard-style spaced repetition

Usage:
  python deeptutor_mcp.py

Environment:
  DEEPTUTOR_BASE_URL  — DeepTutor API base URL (default: http://127.0.0.1:8001)
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = os.environ.get("DEEPTUTOR_BASE_URL", "http://127.0.0.1:8001")
APP_NAME = "deeptutor"
APP_VERSION = "1.0.0"

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(base_url=BASE_URL, timeout=120.0)
        logger.info(f"DeepTutor client initialized against {BASE_URL}")
    return _client


server = Server(APP_NAME)


# ─── Tool Definitions ────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # ── Health & Config ──────────────────────────────────────────
        Tool(
            name="deeptutor_health",
            description="Check DeepTutor API health.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="deeptutor_runtime_topology",
            description="Get DeepTutor system runtime topology (service status overview).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="deeptutor_list_knowledge_bases",
            description="List all available knowledge bases in DeepTutor.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="deeptutor_knowledge_health",
            description="Check knowledge service health.",
            inputSchema={"type": "object", "properties": {}},
        ),
        # ── Knowledge Base (RAG) ─────────────────────────────────────
        Tool(
            name="deeptutor_create_knowledge_base",
            description=(
                "Create a new knowledge base in DeepTutor for RAG. "
                "Returns a kb_name to use for subsequent upload/query operations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {
                        "type": "string",
                        "description": "Unique name for the knowledge base",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description of the knowledge base",
                    },
                },
                "required": ["kb_name"],
            },
        ),
        Tool(
            name="deeptutor_upload_to_knowledge",
            description=(
                "Upload content to a DeepTutor knowledge base. Supports raw text, "
                "URLs, or file content. The knowledge base will parse and index it for RAG."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {
                        "type": "string",
                        "description": "Knowledge base name",
                    },
                    "content": {
                        "type": "string",
                        "description": "Text content to upload",
                    },
                    "source": {
                        "type": "string",
                        "description": "Optional source identifier (e.g., URL, filename)",
                    },
                },
                "required": ["kb_name", "content"],
            },
        ),
        Tool(
            name="deeptutor_sync_knowledge_config",
            description=(
                "Sync the knowledge base configuration — ensures the knowledge "
                "service is properly configured and synchronized."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        # ── TutorBot ─────────────────────────────────────────────────
        Tool(
            name="deeptutor_create_tutorbot",
            description=(
                "Create a new TutorBot — an AI tutor with a custom SOUL (personality/instruction). "
                "You can define the tutor's personality, expertise, and teaching style."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the tutor bot",
                    },
                    "soul": {
                        "type": "string",
                        "description": "SOUL definition — the tutor's personality, expertise, "
                                      "and teaching instructions (markdown or structured text)",
                    },
                    "model": {
                        "type": "string",
                        "description": "Optional model name to use",
                    },
                },
                "required": ["name", "soul"],
            },
        ),
        Tool(
            name="deeptutor_list_tutorbots",
            description="List all available TutorBots.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="deeptutor_tutorbot_chat",
            description=(
                "Send a message to a TutorBot for interactive tutoring. "
                "Returns the tutor's response. Use for explaining concepts, "
                "answering questions, or guided learning."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "bot_id": {
                        "type": "string",
                        "description": "TutorBot ID (from deeptutor_list_tutorbots)",
                    },
                    "message": {
                        "type": "string",
                        "description": "Your question or topic to discuss with the tutor",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for conversation continuity",
                    },
                },
                "required": ["bot_id", "message"],
            },
        ),
        Tool(
            name="deeptutor_tutorbot_recent",
            description="Get recent TutorBot interactions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max entries to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        # ── Co-Writer ────────────────────────────────────────────────
        Tool(
            name="deeptutor_cowriter_edit",
            description=(
                "Send a writing task to DeepTutor's Co-Writer for interactive "
                "learning-by-writing with AI feedback. "
                "The AI will review, annotate, and provide feedback on your writing."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text or writing to be reviewed",
                    },
                    "task": {
                        "type": "string",
                        "description": "The writing task or goal (e.g., 'review my essay', "
                                      "'check my code', 'improve my explanation')",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID",
                    },
                },
                "required": ["text", "task"],
            },
        ),
        Tool(
            name="deeptutor_cowriter_edit_react",
            description=(
                "Co-Writer with React-style streaming — returns AI feedback "
                "in a stream for real-time interaction."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to review",
                    },
                    "task": {
                        "type": "string",
                        "description": "The writing task or goal",
                    },
                },
                "required": ["text", "task"],
            },
        ),
        # ── Book ─────────────────────────────────────────────────────
        Tool(
            name="deeptutor_book_deep_dive",
            description=(
                "Initiate a deep-dive session on a topic in a DeepTutor Book. "
                "Returns structured learning content with explanations, examples, and quiz questions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "string",
                        "description": "Book ID",
                    },
                    "topic": {
                        "type": "string",
                        "description": "Topic or chapter to deep-dive into",
                    },
                },
                "required": ["book_id", "topic"],
            },
        ),
        Tool(
            name="deeptutor_book_supplement",
            description=(
                "Get supplemental content for a topic in a DeepTutor Book — "
                "additional explanations, resources, or related materials."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "string",
                        "description": "Book ID",
                    },
                    "topic": {
                        "type": "string",
                        "description": "Topic for supplemental content",
                    },
                },
                "required": ["book_id", "topic"],
            },
        ),
        Tool(
            name="deeptutor_list_books",
            description="List all DeepTutor Books.",
            inputSchema={"type": "object", "properties": {}},
        ),
        # ── Notebook ─────────────────────────────────────────────────
        Tool(
            name="deeptutor_notebook_create",
            description="Create a new notebook for Q&A note-taking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Notebook title",
                    },
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="deeptutor_notebook_add",
            description=(
                "Add a Q&A entry to a DeepTutor notebook. "
                "DeepTutor will store the question and answer for later review."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "notebook_id": {
                        "type": "string",
                        "description": "Notebook ID",
                    },
                    "question": {
                        "type": "string",
                        "description": "The question",
                    },
                    "answer": {
                        "type": "string",
                        "description": "The answer",
                    },
                },
                "required": ["notebook_id", "question", "answer"],
            },
        ),
        Tool(
            name="deeptutor_notebook_add_with_summary",
            description=(
                "Add a Q&A entry to a notebook and get AI-generated summary/insights "
                "from DeepTutor on the added content."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "notebook_id": {
                        "type": "string",
                        "description": "Notebook ID",
                    },
                    "question": {
                        "type": "string",
                        "description": "The question",
                    },
                    "answer": {
                        "type": "string",
                        "description": "The answer",
                    },
                },
                "required": ["notebook_id", "question", "answer"],
            },
        ),
        Tool(
            name="deeptutor_notebook_list",
            description="List all notebooks.",
            inputSchema={"type": "object", "properties": {}},
        ),
        # ── Question Notebook (Spaced Repetition) ────────────────────
        Tool(
            name="deeptutor_qna_lookup",
            description=(
                "Look up a question in DeepTutor's question notebook. "
                "Returns existing Q&A entries matching the query."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question text to look up",
                    },
                },
                "required": ["question"],
            },
        ),
        Tool(
            name="deeptutor_qna_upsert",
            description=(
                "Add or update a question-answer entry in DeepTutor's "
                "question notebook for spaced repetition learning."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question",
                    },
                    "answer": {
                        "type": "string",
                        "description": "The answer",
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional categories/tags for the entry",
                    },
                },
                "required": ["question", "answer"],
            },
        ),
        # ── Sessions ──────────────────────────────────────────────────
        Tool(
            name="deeptutor_get_session",
            description="Get a DeepTutor session by ID (includes history).",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID",
                    },
                },
                "required": ["session_id"],
            },
        ),
    ]


# ─── Tool Handler ─────────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    try:
        client = get_client()

        # ── Health & Topology ────────────────────────────────────────
        if name == "deeptutor_health":
            resp = await client.get("/")
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_runtime_topology":
            resp = await client.get("/api/v1/system/runtime-topology")
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        # ── Knowledge Base ───────────────────────────────────────────
        elif name == "deeptutor_list_knowledge_bases":
            resp = await client.get("/api/v1/knowledge/list")
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_knowledge_health":
            resp = await client.get("/api/v1/knowledge/health")
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_create_knowledge_base":
            payload = {"kb_name": arguments["kb_name"]}
            if "description" in arguments:
                payload["description"] = arguments["description"]
            resp = await client.post("/api/v1/knowledge/create", json=payload)
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_upload_to_knowledge":
            kb_name = arguments["kb_name"]
            # Determine content type — check if it looks like a URL
            content = arguments["content"]
            payload: dict[str, Any] = {"content": content}
            if arguments.get("source"):
                payload["source"] = arguments["source"]
            resp = await client.post(f"/api/v1/knowledge/{kb_name}/upload", json=payload)
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_sync_knowledge_config":
            resp = await client.post("/api/v1/knowledge/configs/sync", json={})
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        # ── TutorBot ─────────────────────────────────────────────────
        elif name == "deeptutor_list_tutorbots":
            resp = await client.get("/api/v1/tutorbot/souls")
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_create_tutorbot":
            payload: dict[str, Any] = {
                "name": arguments["name"],
                "soul": arguments["soul"],
            }
            if "model" in arguments:
                payload["model"] = arguments["model"]
            resp = await client.post("/api/v1/tutorbot/souls", json=payload)
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_tutorbot_chat":
            payload: dict[str, Any] = {"message": arguments["message"]}
            if arguments.get("session_id"):
                payload["session_id"] = arguments["session_id"]
            bot_id = arguments["bot_id"]
            resp = await client.post(f"/api/v1/tutorbot/{bot_id}", json=payload)
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_tutorbot_recent":
            limit = arguments.get("limit", 10)
            resp = await client.get("/api/v1/tutorbot/recent", params={"limit": limit})
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        # ── Co-Writer ────────────────────────────────────────────────
        elif name == "deeptutor_cowriter_edit":
            payload: dict[str, Any] = {
                "text": arguments["text"],
                "task": arguments["task"],
            }
            if arguments.get("session_id"):
                payload["session_id"] = arguments["session_id"]
            resp = await client.post("/api/v1/co_writer/edit", json=payload)
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_cowriter_edit_react":
            payload = {
                "text": arguments["text"],
                "task": arguments["task"],
            }
            resp = await client.post("/api/v1/co_writer/edit_react", json=payload)
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        # ── Book ─────────────────────────────────────────────────────
        elif name == "deeptutor_list_books":
            resp = await client.get("/api/v1/book/books")
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_book_deep_dive":
            payload = {"topic": arguments["topic"]}
            resp = await client.post(
                f"/api/v1/book/books/{arguments['book_id']}/deep-dive",
                json=payload,
            )
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_book_supplement":
            payload = {"topic": arguments["topic"]}
            resp = await client.post(
                f"/api/v1/book/books/{arguments['book_id']}/supplement",
                json=payload,
            )
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        # ── Notebook ─────────────────────────────────────────────────
        elif name == "deeptutor_notebook_create":
            payload = {"title": arguments["title"]}
            resp = await client.post("/api/v1/notebook/create", json=payload)
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_notebook_add":
            payload = {
                "question": arguments["question"],
                "answer": arguments["answer"],
            }
            resp = await client.post(
                f"/api/v1/notebook/{arguments['notebook_id']}/add_record",
                json=payload,
            )
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_notebook_add_with_summary":
            payload = {
                "question": arguments["question"],
                "answer": arguments["answer"],
            }
            resp = await client.post(
                f"/api/v1/notebook/{arguments['notebook_id']}/add_record_with_summary",
                json=payload,
            )
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_notebook_list":
            resp = await client.get("/api/v1/notebook/list")
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        # ── Question Notebook ────────────────────────────────────────
        elif name == "deeptutor_qna_lookup":
            resp = await client.get(
                "/api/v1/question-notebook/entries/lookup/by-question",
                params={"question": arguments["question"]},
            )
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        elif name == "deeptutor_qna_upsert":
            payload: dict[str, Any] = {
                "question": arguments["question"],
                "answer": arguments["answer"],
            }
            if arguments.get("categories"):
                payload["categories"] = arguments["categories"]
            resp = await client.post("/api/v1/question-notebook/entries/upsert", json=payload)
            return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]

        # ── Sessions ─────────────────────────────────────────────────
        elif name == "deeptutor_get_session":
            resp = await client.get(f"/api/v1/sessions/{arguments['session_id']}")
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
    logger.info(f"DeepTutor MCP Server starting (base_url: {BASE_URL})")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

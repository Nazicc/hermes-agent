#!/usr/bin/env python3
"""
SimpleMem MCP Server — Exposes SimpleMem long-term memory as MCP tools.

Architecture:
  Hermes Agent → MCP Client → simplemem_mcp.py (this server)
                                    ↓
                              SimpleMemSystem (LanceDB + embeddings)

Usage:
  python simplemem_mcp.py

Environment:
  SIMPLEMEM_DATA_DIR   — Data directory (default: ~/.hermes/simplemem-data)
  SIMPLEMEM_EMBEDDING_MODEL — Embedding model (default: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

APP_NAME = "simplemem"
APP_VERSION = "1.0.0"

DATA_DIR = os.environ.get("SIMPLEMEM_DATA_DIR", os.path.expanduser("~/.hermes/simplemem-data"))
EMBEDDING_MODEL = os.environ.get(
    "SIMPLEMEM_EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# Lazy system instance
_system = None


def get_system():
    global _system
    if _system is None:
        from simplemem import create_system
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
        _system = create_system()
        logger.info(f"SimpleMem system initialized, data_dir={DATA_DIR}")
    return _system


app = Server(APP_NAME)


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="search_memories",
            description="Semantic search over long-term memories. Returns top-k most relevant memory entries.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "description": "Number of results (default 5)", "default": 5},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="add_memory",
            description="Add a new memory entry to long-term storage.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Memory text to store"},
                    "metadata": {"type": "object", "description": "Optional metadata dict"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="session_search",
            description="Search long-term memories with synthesis — retrieves context and generates a summary answer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results (default 5)", "default": 5},
                },
                "required": ["query"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    system = get_system()

    if name == "search_memories":
        query = arguments["query"]
        top_k = arguments.get("top_k", 5)
        try:
            results = system.search(query, top_k=top_k)
            return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]
        except Exception as e:
            logger.error(f"search_memories error: {e}")
            return [TextContent(type="text", text=f"Error: {e}")]

    elif name == "add_memory":
        text = arguments["text"]
        metadata = arguments.get("metadata", {})
        try:
            entry = {"text": text, "metadata": metadata}
            system.add_entry(entry)
            return [TextContent(type="text", text=f"Memory added: {text[:80]}...")]
        except Exception as e:
            logger.error(f"add_memory error: {e}")
            return [TextContent(type="text", text=f"Error: {e}")]

    elif name == "session_search":
        query = arguments["query"]
        limit = arguments.get("limit", 5)
        try:
            messages = [{"role": "user", "content": query}]
            result = system.synthesize(messages)
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            # Fallback to basic search if synthesize fails
            try:
                results = system.search(query, top_k=limit)
                return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]
            except Exception as e2:
                logger.error(f"session_search error: {e}, fallback error: {e2}")
                return [TextContent(type="text", text=f"Error: {e2}")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

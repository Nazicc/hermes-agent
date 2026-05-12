#!/usr/bin/env python3
"""
Hindsight MCP Server — wraps Vectorize/Hindsight as a FastMCP server for hermes.
Exposes: retain, recall, reflect, list_banks, get_bank_profile
Bank: hermes-agent (all Hermes memories in one bank)
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# ── Load ~/.hermes/.env ─────────────────────────────────────────────────────
_ENV_PATH = Path.home() / ".hermes" / ".env"
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# ── Defaults ───────────────────────────────────────────────────────────────
HINDSIGHT_BASE_URL = os.environ.get("HINDSIGHT_API_URL", "http://localhost:18888")
MINIMAX_API_KEY = os.environ.get("MINIMAX_CN_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
MINIMAX_BASE_URL = os.environ.get("MINIMAX_CN_BASE_URL", "https://api.minimaxi.com/anthropic")
DEFAULT_BANK = "hermes-agent"

# ── Lazy Hindsight client ──────────────────────────────────────────────────
_HINDSIGHT_CLIENT = None


def _get_client():
    global _HINDSIGHT_CLIENT
    if _HINDSIGHT_CLIENT is None:
        from hindsight_client import Hindsight

        _HINDSIGHT_CLIENT = Hindsight(
            base_url=HINDSIGHT_BASE_URL,
            api_key=MINIMAX_API_KEY,
            timeout=300.0,
        )
    return _HINDSIGHT_CLIENT


# ── FastMCP server ─────────────────────────────────────────────────────────
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="hindsight",
    instructions="Agent memory system with retain/recall/reflect. "
                 "Use bank_id='hermes-agent' for all Hermes Agent memories. "
                 "retain: store facts. recall: search. reflect: deep analysis.",
)


# ── Tools ──────────────────────────────────────────────────────────────────

@mcp.tool()
def retain(
    content: str,
    bank_id: str = DEFAULT_BANK,
    context: str | None = None,
    timestamp: str | None = None,
    tags: list[str] | None = None,
) -> str:
    """
    Store a memory (fact, experience, or piece of information) in Hindsight.

    Args:
        content: The information to remember. Can be a fact, experience, or any text.
        bank_id: Memory bank ID (default: hermes-agent)
        context: Optional context hint for better recall (e.g., 'project-X', 'user-preference')
        timestamp: Optional ISO timestamp (auto-generated if omitted)
        tags: Optional list of tags for filtering (e.g., ['user', 'code', 'decision'])
    """
    client = _get_client()
    try:
        ts = None
        if timestamp:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        response = client.retain(
            bank_id=bank_id,
            content=content,
            context=context,
            timestamp=ts,
            tags=tags,
        )
        return json.dumps(
            {
                "status": "stored",
                "memory_id": response.memory_id,
                "bank_id": bank_id,
                "content_preview": content[:100] + ("..." if len(content) > 100 else ""),
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def recall(
    query: str,
    bank_id: str = DEFAULT_BANK,
    max_tokens: int = 4096,
    budget: str = "mid",
    types: list[str] | None = None,
    tags: list[str] | None = None,
    tags_match: str = "any",
    max_results: int = 10,
) -> str:
    """
    Retrieve relevant memories from Hindsight using multi-strategy retrieval
    (semantic + BM25 + graph + temporal).

    Args:
        query: Natural-language search query
        bank_id: Memory bank ID (default: hermes-agent)
        max_tokens: Max context tokens to return (default: 4096)
        budget: 'low'|'mid'|'high' — controls retrieval thoroughness
        types: Filter by memory types (e.g., ['experience', 'fact'])
        tags: Filter by tags
        tags_match: 'any'|'all' — match any or all tags
        max_results: Number of top results to return (default: 10)
    """
    client = _get_client()
    try:
        response = client.recall(
            bank_id=bank_id,
            query=query,
            types=types,
            max_tokens=max_tokens,
            budget=budget,
            tags=tags,
            tags_match=tags_match,
        )

        # Parse response — recall returns structured results
        results = []
        try:
            items = list(response) if hasattr(response, "__iter__") else [response]
            for item in items[:max_results]:
                if hasattr(item, "content"):
                    results.append(
                        {
                            "type": getattr(item, "type", "unknown"),
                            "content": item.content,
                            "score": getattr(item, "score", None),
                        }
                    )
        except Exception:
            # Fallback: try to stringify
            results = [{"raw": str(response)}]

        return json.dumps(
            {
                "status": "ok",
                "query": query,
                "bank_id": bank_id,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def reflect(
    query: str,
    bank_id: str = DEFAULT_BANK,
    budget: str = "low",
    context: str | None = None,
    max_tokens: int | None = None,
    include_facts: bool = True,
    exclude_mental_models: bool = False,
) -> str:
    """
    Deep reflection on memories — generate insights, connect patterns,
    and form new understanding from existing memories.

    Use when: analyzing past experiences, generating summaries,
    understanding user preferences deeply, or answering complex questions
    that require synthesis across multiple memories.

    Args:
        query: The question or topic to reflect on
        bank_id: Memory bank ID (default: hermes-agent)
        budget: 'low'|'mid'|'high' — compute/quality budget
        context: Optional additional context
        max_tokens: Max response tokens
        include_facts: Include supporting facts in response
        exclude_mental_models: Skip inferred mental models
    """
    client = _get_client()
    try:
        response = client.reflect(
            bank_id=bank_id,
            query=query,
            budget=budget,
            context=context,
            max_tokens=max_tokens,
            include_facts=include_facts,
            exclude_mental_models=exclude_mental_models,
        )

        # Parse reflect response
        insights = []
        try:
            if hasattr(response, "text") and response.text:
                insights = [{"content": response.text, "type": "reflection"}]
            elif hasattr(response, "insights") and response.insights:
                for insight in response.insights:
                    insights.append(
                        {
                            "content": getattr(insight, "content", str(insight)),
                            "type": getattr(insight, "type", "insight"),
                        }
                    )
            elif hasattr(response, "facts") and response.facts:
                for fact in response.facts:
                    insights.append(
                        {
                            "content": getattr(fact, "content", str(fact)),
                            "type": "fact",
                        }
                    )
            else:
                insights = [{"content": str(response)}]
        except Exception:
            insights = [{"content": str(response)}]

        return json.dumps(
            {
                "status": "ok",
                "query": query,
                "bank_id": bank_id,
                "insights": insights,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def list_banks(bank_prefix: str = "hermes") -> str:
    """
    List all memory banks available to the current user.
    Useful for debugging and memory organization.

    Args:
        bank_prefix: Filter banks by prefix (default: 'hermes')
    """
    # Hindsight client doesn't expose a list_banks API directly.
    # Return the known default bank info.
    return json.dumps(
        {
            "status": "ok",
            "default_bank": DEFAULT_BANK,
            "note": "Hindsight cloud API does not expose multi-bank listing. "
                    "All Hermes memories use bank_id='hermes-agent'.",
        },
        ensure_ascii=False,
    )


@mcp.tool()
def get_bank_profile(bank_id: str = DEFAULT_BANK) -> str:
    """
    Get statistics and configuration for a memory bank.

    Args:
        bank_id: Memory bank ID (default: hermes-agent)
    """
    try:
        import urllib.request

        base = HINDSIGHT_BASE_URL.rstrip("/")
        # Fetch stats
        stats_resp = urllib.request.urlopen(
            f"{base}/v1/default/banks/{bank_id}/stats", timeout=10
        )
        stats = json.loads(stats_resp.read().decode())
        # Fetch profile (disposition)
        profile_resp = urllib.request.urlopen(
            f"{base}/v1/default/banks/{bank_id}/profile", timeout=10
        )
        profile = json.loads(profile_resp.read().decode())

        return json.dumps(
            {
                "status": "ok",
                "bank_id": bank_id,
                "stats": stats,
                "profile": profile,
            },
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


@mcp.tool()
def health_check() -> str:
    """
    Check if Hindsight Docker container and API are running.
    """
    try:
        import httpx

        resp = httpx.get(f"{HINDSIGHT_BASE_URL}/health", timeout=10)
        return json.dumps(
            {
                "status": "ok" if resp.status_code == 200 else "degraded",
                "http_status": resp.status_code,
                "body": resp.text[:200],
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Hindsight unreachable: {e}"})


# ── Stdio transport ────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")

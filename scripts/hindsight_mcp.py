#!/usr/bin/env python3
"""
Hindsight MCP Server — wraps Vectorize/Hindsight REST API as a FastMCP server for hermes.
Exposes: retain, recall, reflect, list_banks, get_bank_profile, health_check
Bank: hermes-agent (all Hermes memories in one bank)

Uses direct REST API calls via urllib — no hindsight_client dependency.
"""
import os
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
DEFAULT_BANK = "hermes-agent"

log = logging.getLogger("hindsight_mcp")


# ── REST helpers ──────────────────────────────────────────────────────────
def _api(method: str, path: str, body: dict | None = None, timeout: int = 30) -> dict:
    """Call Hindsight REST API and return parsed JSON dict."""
    import urllib.request
    import urllib.error

    base = HINDSIGHT_BASE_URL.rstrip("/")
    url = f"{base}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method.upper())
    req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:500]
        return {"status": "error", "http_code": e.code, "message": err_body}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── FastMCP server ────────────────────────────────────────────────────────
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="hindsight",
    instructions="Agent memory system with retain/recall/reflect. "
                 "Use bank_id='hermes-agent' for all Hermes Agent memories. "
                 "retain: store facts. recall: search. reflect: deep analysis.",
)


# ── Tools ─────────────────────────────────────────────────────────────────

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
    body: dict = {"content": content}
    if context:
        body["context"] = context
    if timestamp:
        body["occurred_at"] = timestamp
    if tags:
        body["tags"] = tags

    resp = _api("POST", f"/v1/default/banks/{bank_id}/memories", body)
    if resp.get("status") == "error":
        return json.dumps(resp, ensure_ascii=False)

    # Extract memory_id from response
    memory_id = resp.get("id") or resp.get("memory_id") or "unknown"
    return json.dumps(
        {
            "status": "stored",
            "memory_id": memory_id,
            "bank_id": bank_id,
            "content_preview": content[:100] + ("..." if len(content) > 100 else ""),
        },
        ensure_ascii=False,
    )


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
    body: dict = {"query": query, "max_tokens": max_tokens}
    if budget:
        body["budget"] = budget
    if types:
        body["types"] = types
    if tags:
        body["tags"] = tags
    if tags_match:
        body["tags_match"] = tags_match

    resp = _api("POST", f"/v1/default/banks/{bank_id}/memories/recall", body, timeout=60)
    if resp.get("status") == "error":
        return json.dumps(resp, ensure_ascii=False)

    results = resp.get("results", [])[:max_results]
    # Compress each result for context efficiency
    compact = []
    for r in results:
        compact.append({
            "type": r.get("type", "unknown"),
            "text": r.get("text", "")[:500],
            "tags": r.get("tags", []),
            "occurred": r.get("occurred_start", ""),
        })

    return json.dumps(
        {
            "status": "ok",
            "query": query,
            "bank_id": bank_id,
            "count": len(compact),
            "results": compact,
        },
        ensure_ascii=False,
        indent=2,
    )


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
    body: dict = {"query": query, "budget": budget}
    if context:
        body["context"] = context
    if max_tokens:
        body["max_tokens"] = max_tokens
    body["include_facts"] = include_facts
    body["exclude_mental_models"] = exclude_mental_models

    resp = _api("POST", f"/v1/default/banks/{bank_id}/reflect", body, timeout=120)
    if resp.get("status") == "error":
        return json.dumps(resp, ensure_ascii=False)

    return json.dumps(
        {
            "status": "ok",
            "query": query,
            "bank_id": bank_id,
            "text": resp.get("text", ""),
            "usage": resp.get("usage"),
        },
        ensure_ascii=False,
    )


@mcp.tool()
def list_banks(bank_prefix: str = "hermes") -> str:
    """
    List all memory banks available to the current user.
    Useful for debugging and memory organization.

    Args:
        bank_prefix: Filter banks by prefix (default: 'hermes')
    """
    resp = _api("GET", "/v1/default/banks")
    if resp.get("status") == "error":
        return json.dumps(resp, ensure_ascii=False)

    banks = resp.get("banks", [])
    if bank_prefix:
        banks = [b for b in banks if b.get("bank_id", "").startswith(bank_prefix)]

    return json.dumps(
        {"status": "ok", "count": len(banks), "banks": banks},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def get_bank_profile(bank_id: str = DEFAULT_BANK) -> str:
    """
    Get statistics and configuration for a memory bank.

    Args:
        bank_id: Memory bank ID (default: hermes-agent)
    """
    profile = _api("GET", f"/v1/default/banks/{bank_id}/profile")
    stats = _api("GET", f"/v1/default/banks/{bank_id}/stats")

    err_p = profile.get("status") == "error"
    err_s = stats.get("status") == "error"
    if err_p and err_s:
        return json.dumps({"status": "error", "message": f"profile: {profile.get('message')}; stats: {stats.get('message')}"}, ensure_ascii=False)

    result = {"status": "ok", "bank_id": bank_id}
    if not err_p:
        result["profile"] = profile
    if not err_s:
        result["stats"] = stats

    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def health_check() -> str:
    """
    Check if Hindsight Docker container and API are running.
    """
    import urllib.request
    import urllib.error

    try:
        resp = urllib.request.urlopen(f"{HINDSIGHT_BASE_URL}/health", timeout=10)
        data = json.loads(resp.read().decode())
        return json.dumps(
            {"status": "ok" if data.get("status") == "healthy" else "degraded", "body": data},
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Hindsight unreachable: {e}"})


# ── Stdio transport ────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")

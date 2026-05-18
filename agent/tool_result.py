"""
ToolResult — structured tool execution output.

Lightweight dataclass that captures what the tool returned (content),
how long it took (duration), and whether it succeeded (status/error).

This is the foundation for:
  1. Better error propagation to the LLM prompt
  2. Session event logging (Step 2)
  3. Context reconstruction from event log (Step 3)

Design principle: minimal invasiveness.
  - Tool handlers still return plain strings (backward compatible).
  - handle_function_call() wraps the string into a ToolResult.
  - The caller extracts .content for the message dict (unchanged).
  - Metadata fields (_tool_duration, _tool_status, _tool_error) are
    embedded in the in-memory message dict but not persisted to SQLite
    until Step 2 adds a dedicated event log.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Structured result of a single tool execution."""

    # ── Identity ──────────────────────────────────────────────────────
    name: str                # function / tool name
    call_id: str             # tool_call_id from the model

    # ── Output ────────────────────────────────────────────────────────
    content: str = ""        # The actual tool output (same raw string as today)
    truncated: bool = False  # True if content was truncated for the prompt

    # ── Status ────────────────────────────────────────────────────────
    status: str = "success"  # "success" | "error"
    error: str = ""          # Human-readable error message (empty on success)

    # ── Timing ────────────────────────────────────────────────────────
    duration_ms: float = 0.0  # Wall-clock execution time in milliseconds
    started_at: float = 0.0   # time.monotonic() at start

    # ── Extras ────────────────────────────────────────────────────────
    metadata: dict[str, Any] = field(default_factory=dict)

    # ── Factories ─────────────────────────────────────────────────────

    @classmethod
    def from_execution(
        cls,
        name: str,
        call_id: str,
        content: str,
        *,
        started_at: float = 0.0,
        duration_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Wrap a raw tool output, auto-detecting errors."""
        # If duration wasn't provided, compute it
        if duration_ms <= 0 and started_at > 0:
            duration_ms = (time.monotonic() - started_at) * 1000.0

        status = "success"
        error = ""
        if isinstance(content, str):
            # Common error patterns from handlers
            _lower = content.strip().lower()
            if _lower.startswith("error:"):
                status = "error"
                error = content
            elif _lower.startswith("error -"):
                status = "error"
                error = content
            else:
                # Try JSON parse — some handlers return {"error": "..."}
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict) and "error" in parsed:
                        status = "error"
                        error = str(parsed["error"])
                except (json.JSONDecodeError, TypeError):
                    pass

        return cls(
            name=name,
            call_id=call_id,
            content=content,
            status=status,
            error=error,
            duration_ms=duration_ms,
            started_at=started_at,
            metadata=metadata or {},
        )

    @classmethod
    def from_error(
        cls,
        name: str,
        call_id: str,
        error_msg: str,
        *,
        duration_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Create an error result without auto-detection."""
        return cls(
            name=name,
            call_id=call_id,
            content=error_msg,
            status="error",
            error=error_msg,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

    # ── Accessors ─────────────────────────────────────────────────────

    @property
    def is_success(self) -> bool:
        return self.status == "success"

    @property
    def is_error(self) -> bool:
        return self.status == "error"

    @property
    def duration_s(self) -> float:
        """Duration in seconds (for display/logging)."""
        return self.duration_ms / 1000.0

    # ── Serialization ─────────────────────────────────────────────────

    def to_message_dict(self) -> dict[str, Any]:
        """Build the OpenAI-style tool message dict (current format).

        The standard fields (role, name, content, tool_call_id) are
        identical to today's format.  Hidden metadata is embedded as
        ``_tool_*`` fields for internal use and later event-logging.
        """
        return {
            "role": "tool",
            "name": self.name,
            "content": self.content,
            "tool_call_id": self.call_id,
            "_tool_status": self.status,
            "_tool_duration": self.duration_ms,
            "_tool_error": self.error,
            "_tool_truncated": self.truncated,
        }

    def to_dict(self) -> dict[str, Any]:
        """Plain dict for event-log / serialization."""
        return {
            "name": self.name,
            "call_id": self.call_id,
            "content": self.content,
            "status": self.status,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "truncated": self.truncated,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """JSON string for event-log persistence."""
        return json.dumps({
            "name": self.name,
            "call_id": self.call_id,
            "content": self.content,
            "status": self.status,
            "error": self.error,
            "duration_ms": self.duration_ms,
        })

    def to_prompt_fragment(self) -> str:
        """Markdown-formatted summary for prompt injection / debugging.

        Example::

            **Tool: search_web** (1.23s) ✅
            > result content preview...
        """
        icon = "✅" if self.is_success else "❌"
        preview = (self.content[:200] + "…") if len(self.content) > 200 else self.content
        parts = [
            f"**Tool: {self.name}** ({self.duration_s:.2f}s) {icon}",
            f"> {preview}",
        ]
        if self.is_error:
            parts.append(f"> **Error**: {self.error}")
        return "\n".join(parts)

    def __str__(self) -> str:
        return self.content

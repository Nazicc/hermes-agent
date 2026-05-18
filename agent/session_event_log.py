"""
Session Event Log — structured, append-only event log for agent sessions.

Inspired by Claude's Managed Agent architecture: instead of storing messages
as flat SQLite rows, each significant event in a session is recorded as a
structured JSONL entry. This enables:

- **Replay**: reconstruct full context from the event log
- **Self-analysis**: analyze tool durations, error patterns, LLM latency
- **Harness isolation**: the event log, not in-memory state, drives the session

Usage:
    log = SessionEventLog(session_id="sess_abc123", base_dir=Path(...))
    log.append("tool_call", {"name": "terminal", "args": {"command": "ls"}})
    log.append("tool_result", {"name": "terminal", "status": "success", "duration_ms": 42.0, ...})
    for event in log.replay(event_types=["tool_call", "tool_result"]):
        print(event.event_type, event.data)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterator, List, Optional


# ── Event types ──────────────────────────────────────────────────────────────

# Session lifecycle
SESSION_START = "session_start"
SESSION_END = "session_end"
SESSION_COMPRESSION = "session_compression"

# Brain (LLM) events
BRAIN_INVOKE = "brain_invoke"       # LLM API call start
BRAIN_RESPONSE = "brain_response"   # LLM API call result (with usage, latency)
BRAIN_ERROR = "brain_error"         # LLM API call failure

# Tool events
TOOL_CALL = "tool_call"             # LLM requested a tool call
TOOL_RESULT = "tool_result"         # Tool execution completed (with metadata)
TOOL_BLOCKED = "tool_blocked"       # Tool blocked by guardrail/plugin

# User events
USER_MESSAGE = "user_message"       # User sent a message
ASSISTANT_MESSAGE = "assistant_message"  # Assistant text response (non-tool)


# ── Event data class ──────────────────────────────────────────────────────────

@dataclass
class SessionEvent:
    """A single event in the session event log."""

    event_type: str
    session_id: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    sequence: int = 0

    def to_json(self) -> str:
        """Serialize to a JSONL line."""
        d = asdict(self)
        return json.dumps(d, ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, line: str) -> "SessionEvent":
        """Deserialize from a JSONL line."""
        d = json.loads(line)
        return cls(
            event_type=d["event_type"],
            session_id=d["session_id"],
            data=d.get("data", {}),
            timestamp=d.get("timestamp", 0.0),
            sequence=d.get("sequence", 0),
        )


# ── Event log ────────────────────────────────────────────────────────────────

class SessionEventLog:
    """Append-only, structured event log for a single session.

    Persisted as a JSONL file at ``{base_dir}/{session_id}/events.jsonl``.
    Thread-safe for appends (opens+appends+closes on each call — no lock needed).
    """

    def __init__(self, session_id: str, base_dir: Optional[Path] = None) -> None:
        self.session_id = session_id
        if base_dir is None:
            base_dir = Path.home() / ".hermes" / "sessions"
        self.base_dir = Path(base_dir)
        self._session_dir = self.base_dir / session_id
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._path = self._session_dir / "events.jsonl"
        self._sequence: int = 0
        self._load_sequence()

    # ── Public API ───────────────────────────────────────────────────────────

    def append(self, event_type: str, data: dict[str, Any], *, timestamp: Optional[float] = None) -> SessionEvent:
        """Append a new event to the log. Returns the created event."""
        self._sequence += 1
        event = SessionEvent(
            event_type=event_type,
            session_id=self.session_id,
            data=data,
            timestamp=timestamp if timestamp is not None else time.time(),
            sequence=self._sequence,
        )
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(event.to_json() + "\n")
        return event

    def replay(
        self,
        *,
        event_types: Optional[list[str]] = None,
        since: Optional[float] = None,
        until: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> list[SessionEvent]:
        """Iterate over all matching events in insertion order.

        Args:
            event_types: Filter by event type(s). None = all types.
            since: Only events after this timestamp (unix seconds).
            until: Only events before this timestamp.
            limit: Max events to return.
        """
        results: list[SessionEvent] = []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    event = SessionEvent.from_json(line)
                    if event_types and event.event_type not in event_types:
                        continue
                    if since is not None and event.timestamp < since:
                        continue
                    if until is not None and event.timestamp > until:
                        continue
                    results.append(event)
                    if limit is not None and len(results) >= limit:
                        break
        except FileNotFoundError:
            pass
        return results

    def count(self, event_type: Optional[str] = None) -> int:
        """Count events, optionally filtered by type."""
        count = 0
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if event_type:
                        try:
                            d = json.loads(line)
                            if d.get("event_type") == event_type:
                                count += 1
                        except json.JSONDecodeError:
                            continue
                    else:
                        count += 1
        except FileNotFoundError:
            pass
        return count

    def clear(self) -> None:
        """Wipe all events. Resets sequence counter."""
        self._path.write_text("")
        self._sequence = 0

    @property
    def path(self) -> Path:
        return self._path

    # ── Internal ─────────────────────────────────────────────────────────────

    def _load_sequence(self) -> None:
        """Restore sequence counter from the last event on disk (crash recovery)."""
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                last_line = None
                for line in f:
                    line = line.strip()
                    if line:
                        last_line = line
                if last_line:
                    d = json.loads(last_line)
                    self._sequence = d.get("sequence", 0)
        except (FileNotFoundError, json.JSONDecodeError):
            self._sequence = 0

    def __len__(self) -> int:
        return self._sequence

    def __repr__(self) -> str:
        return f"<SessionEventLog session={self.session_id!r} events={self._sequence} path={self._path}>"

"""gateway.runners.utils — S1 GatewayUtils extraction.

Pure utility functions extracted from gateway/run.py to reduce the God Object.
All functions are module-level (no ``self`` coupling) and can be imported
directly by tests, other runners, or platform adapters.

Re-exported in gateway/run.py for backward compatibility — external callers
that use ``from gateway.run import _load_gateway_config`` continue to work.
"""

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional

from hermes_constants import get_hermes_home

_hermes_home = get_hermes_home()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Docker volume constants (shared with GatewayRunner._warn_if_docker_…)
# ---------------------------------------------------------------------------
_DOCKER_VOLUME_SPEC_RE = re.compile(
    r"^(?P<host>.+):(?P<container>/[^:]+?)(?::(?P<options>[^:]+))?$"
)
_DOCKER_MEDIA_OUTPUT_CONTAINER_PATHS = {"/output", "/outputs"}

# ---------------------------------------------------------------------------
# Interrupt / control flow constants
# ---------------------------------------------------------------------------
_INTERRUPT_REASON_STOP = "Stop requested"
_INTERRUPT_REASON_RESET = "Session reset requested"
_INTERRUPT_REASON_TIMEOUT = "Execution timed out (inactivity)"
_INTERRUPT_REASON_SSE_DISCONNECT = "SSE client disconnected"
_INTERRUPT_REASON_GATEWAY_SHUTDOWN = "Gateway shutting down"
_INTERRUPT_REASON_GATEWAY_RESTART = "Gateway restarting"

_CONTROL_INTERRUPT_MESSAGES = frozenset(
    {
        _INTERRUPT_REASON_STOP.lower(),
        _INTERRUPT_REASON_RESET.lower(),
        _INTERRUPT_REASON_TIMEOUT.lower(),
        _INTERRUPT_REASON_SSE_DISCONNECT.lower(),
        _INTERRUPT_REASON_GATEWAY_SHUTDOWN.lower(),
        _INTERRUPT_REASON_GATEWAY_RESTART.lower(),
    }
)


# ---------------------------------------------------------------------------
# WhatsApp identifier helpers
# ---------------------------------------------------------------------------
def _normalize_whatsapp_identifier(value: str) -> str:
    """Strip WhatsApp JID/LID syntax down to its stable numeric identifier."""
    return (
        str(value or "")
        .strip()
        .replace("+", "", 1)
        .split(":", 1)[0]
        .split("@", 1)[0]
    )


def _expand_whatsapp_auth_aliases(identifier: str) -> set:
    """Resolve WhatsApp phone/LID aliases using bridge session mapping files."""
    normalized = _normalize_whatsapp_identifier(identifier)
    if not normalized:
        return set()

    session_dir = _hermes_home / "whatsapp" / "session"
    resolved = set()
    queue = [normalized]

    while queue:
        current = queue.pop(0)
        if not current or current in resolved:
            continue

        resolved.add(current)
        for suffix in ("", "_reverse"):
            mapping_path = session_dir / f"lid-mapping-{current}{suffix}.json"
            if not mapping_path.exists():
                continue
            try:
                mapped = _normalize_whatsapp_identifier(
                    json.loads(mapping_path.read_text(encoding="utf-8"))
                )
            except Exception:
                continue
            if mapped and mapped not in resolved:
                queue.append(mapped)

    return resolved


# ---------------------------------------------------------------------------
# Media / event helpers
# ---------------------------------------------------------------------------
def _build_media_placeholder(event) -> str:
    """Build a text placeholder for media-only events so they aren't dropped.

    When a photo/document is queued during active processing and later
    dequeued, only .text is extracted.  If the event has no caption,
    the media would be silently lost.  This builds a placeholder that
    the vision enrichment pipeline will replace with a real description.
    """
    from gateway.platforms.base import MessageType

    parts = []
    media_urls = getattr(event, "media_urls", None) or []
    media_types = getattr(event, "media_types", None) or []
    for i, url in enumerate(media_urls):
        mtype = media_types[i] if i < len(media_types) else ""
        if mtype.startswith("image/") or getattr(event, "message_type", None) == MessageType.PHOTO:
            parts.append(f"[User sent an image: {url}]")
        elif mtype.startswith("audio/"):
            parts.append(f"[User sent audio: {url}]")
        else:
            parts.append(f"[User sent a file: {url}]")
    return "\n".join(parts)


def _dequeue_pending_event(adapter, session_key: str):
    """Consume and return the full pending event for a session.

    Queued follow-ups must preserve their media metadata so they can re-enter
    the normal image/STT/document preprocessing path instead of being reduced
    to a placeholder string.
    """
    return adapter.get_pending_message(session_key)


# ---------------------------------------------------------------------------
# Control interrupt detection
# ---------------------------------------------------------------------------
def _is_control_interrupt_message(message: Optional[str]) -> bool:
    """Return True when an interrupt message is internal control flow."""
    if not message:
        return False
    normalized = " ".join(str(message).strip().split()).lower()
    return normalized in _CONTROL_INTERRUPT_MESSAGES


# ---------------------------------------------------------------------------
# Skill availability check
# ---------------------------------------------------------------------------
def _check_unavailable_skill(command_name: str) -> str | None:
    """Check if a command matches a known-but-inactive skill.

    Returns a helpful message if the skill exists but is disabled or only
    available as an optional install. Returns None if no match found.
    """
    # Normalize: command uses hyphens, skill names may use hyphens or underscores
    normalized = command_name.lower().replace("_", "-")
    try:
        from tools.skills_tool import _get_disabled_skill_names
        from agent.skill_utils import get_all_skills_dirs
        disabled = _get_disabled_skill_names()

        # Check disabled skills across all dirs (local + external)
        for skills_dir in get_all_skills_dirs():
            if not skills_dir.exists():
                continue
            for skill_md in skills_dir.rglob("SKILL.md"):
                if any(part in ('.git', '.github', '.hub') for part in skill_md.parts):
                    continue
                name = skill_md.parent.name.lower().replace("_", "-")
                if name == normalized and name in disabled:
                    return (
                        f"The **{command_name}** skill is installed but disabled.\n"
                        f"Enable it with: `hermes skills config`"
                    )

        # Check optional skills (shipped with repo but not installed)
        from hermes_constants import get_optional_skills_dir
        repo_root = Path(__file__).resolve().parent.parent.parent
        optional_dir = get_optional_skills_dir(repo_root / "optional-skills")
        if optional_dir.exists():
            for skill_md in optional_dir.rglob("SKILL.md"):
                name = skill_md.parent.name.lower().replace("_", "-")
                if name == normalized:
                    # Build install path: official/<category>/<name>
                    rel = skill_md.parent.relative_to(optional_dir)
                    parts = list(rel.parts)
                    install_path = f"official/{'/'.join(parts)}"
                    return (
                        f"The **{command_name}** skill is available but not installed.\n"
                        f"Install it with: `hermes skills install {install_path}`"
                    )
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Platform / session key helpers
# ---------------------------------------------------------------------------
def _platform_config_key(platform) -> str:
    """Map a Platform enum to its config.yaml key (LOCAL→\"cli\", rest→enum value)."""
    from gateway.config import Platform
    return "cli" if platform == Platform.LOCAL else platform.value


def _parse_session_key(session_key: str) -> dict | None:
    """Parse a session key into its component parts.

    Session keys follow the format
    ``agent:main:{platform}:{chat_type}:{chat_id}[:{extra}...]``.
    Returns a dict with ``platform``, ``chat_type``, ``chat_id``, and
    optionally ``thread_id`` keys, or None if the key doesn't match.

    The 6th element is only returned as ``thread_id`` for chat types where
    it is unambiguous (``dm`` and ``thread``).  For group/channel sessions
    the suffix may be a user_id (per-user isolation) rather than a
    thread_id, so we leave ``thread_id`` out to avoid mis-routing.
    """
    parts = session_key.split(":")
    if len(parts) >= 5 and parts[0] == "agent" and parts[1] == "main":
        result = {
            "platform": parts[2],
            "chat_type": parts[3],
            "chat_id": parts[4],
        }
        if len(parts) > 5 and parts[3] in ("dm", "thread"):
            result["thread_id"] = parts[5]
        return result
    return None


def _format_gateway_process_notification(evt: dict) -> str | None:
    """Format a watch pattern event from completion_queue into a [SYSTEM:] message."""
    evt_type = evt.get("type", "completion")
    _sid = evt.get("session_id", "unknown")
    _cmd = evt.get("command", "unknown")

    if evt_type == "watch_disabled":
        return f"[SYSTEM: {evt.get('message', '')}]"

    if evt_type == "watch_match":
        _pat = evt.get("pattern", "?")
        _out = evt.get("output", "")
        _sup = evt.get("suppressed", 0)
        text = (
            f"[SYSTEM: Background process {_sid} matched "
            f"watch pattern \"{_pat}\".\n"
            f"Command: {_cmd}\n"
            f"Matched output:\n{_out}"
        )
        if _sup:
            text += f"\n({_sup} earlier matches were suppressed by rate limit)"
        text += "]"
        return text

    return None


# ---------------------------------------------------------------------------
# Gateway config / model resolution
# ---------------------------------------------------------------------------
def _load_gateway_config() -> dict:
    """Load and parse ~/.hermes/config.yaml, returning {} on any error."""
    try:
        config_path = _hermes_home / 'config.yaml'
        if config_path.exists():
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
    except Exception:
        logger.debug("Could not load gateway config from %s", _hermes_home / 'config.yaml')
    return {}


def _resolve_gateway_model(config: dict | None = None) -> str:
    """Read model from config.yaml — single source of truth.

    Without this, temporary AIAgent instances (memory flush, /compress) fall
    back to the hardcoded default which fails when the active provider is
    openai-codex.
    """
    cfg = config if config is not None else _load_gateway_config()
    model_cfg = cfg.get("model", {})
    if isinstance(model_cfg, str):
        return model_cfg
    elif isinstance(model_cfg, dict):
        return model_cfg.get("default") or model_cfg.get("model") or ""
    return ""


def _resolve_runtime_agent_kwargs() -> dict:
    """Resolve provider credentials for gateway-created AIAgent instances."""
    from hermes_cli.runtime_provider import (
        resolve_runtime_provider,
        format_runtime_provider_error,
    )

    try:
        runtime = resolve_runtime_provider(
            requested=os.getenv("HERMES_INFERENCE_PROVIDER"),
        )
    except Exception as exc:
        raise RuntimeError(format_runtime_provider_error(exc)) from exc

    return {
        "api_key": runtime.get("api_key"),
        "base_url": runtime.get("base_url"),
        "provider": runtime.get("provider"),
        "api_mode": runtime.get("api_mode"),
        "command": runtime.get("command"),
        "args": list(runtime.get("args") or []),
        "credential_pool": runtime.get("credential_pool"),
    }


def _resolve_hermes_bin() -> Optional[list[str]]:
    """Resolve the Hermes update command as argv parts.

    Tries in order:
    1. ``shutil.which("hermes")`` — standard PATH lookup
    2. ``sys.executable -m hermes_cli.main`` — fallback when Hermes is running
       from a venv/module invocation and the ``hermes`` shim is not on PATH

    Returns argv parts ready for quoting/joining, or ``None`` if neither works.
    """
    import shutil

    hermes_bin = shutil.which("hermes")
    if hermes_bin:
        return [hermes_bin]

    try:
        import importlib.util

        if importlib.util.find_spec("hermes_cli") is not None:
            return [sys.executable, "-m", "hermes_cli.main"]
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# Setup skill check (static)
# ---------------------------------------------------------------------------
def _has_setup_skill() -> bool:
    """Check if the hermes-agent-setup skill is installed."""
    try:
        from tools.skill_manager_tool import _find_skill
        return _find_skill("hermes-agent-setup") is not None
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Adapter TTS helpers (static)
# ---------------------------------------------------------------------------
def _set_adapter_auto_tts_disabled(adapter, chat_id: str, disabled: bool) -> None:
    """Update an adapter's in-memory auto-TTS suppression set if present."""
    disabled_chats = getattr(adapter, "_auto_tts_disabled_chats", None)
    if not isinstance(disabled_chats, set):
        return
    if disabled:
        disabled_chats.add(chat_id)
    else:
        disabled_chats.discard(chat_id)


def _sync_voice_mode_state_to_adapter(adapter, voice_mode: dict) -> None:
    """Restore persisted /voice off state into a live platform adapter."""
    disabled_chats = getattr(adapter, "_auto_tts_disabled_chats", None)
    if not isinstance(disabled_chats, set):
        return
    disabled_chats.clear()
    disabled_chats.update(
        chat_id for chat_id, mode in voice_mode.items() if mode == "off"
    )


# ---------------------------------------------------------------------------
# Docker media delivery warning
# ---------------------------------------------------------------------------
def warn_docker_media_risky(config) -> None:
    """Warn when Docker-backed gateways lack an explicit export mount.

    MEDIA delivery happens in the gateway process, so paths emitted by the model
    must be readable from the host. A plain container-local path like
    ``/workspace/report.txt`` or ``/output/report.txt`` often exists only inside
    Docker, so users commonly need a dedicated export mount such as
    ``host-dir:/output``.
    """
    if os.getenv("TERMINAL_ENV", "").strip().lower() != "docker":
        return

    connected = config.get_connected_platforms()
    messaging_platforms = [p for p in connected if p not in {Platform.LOCAL, Platform.API_SERVER, Platform.WEBHOOK}]
    if not messaging_platforms:
        return

    raw_volumes = os.getenv("TERMINAL_DOCKER_VOLUMES", "").strip()
    volumes: List[str] = []
    if raw_volumes:
        try:
            parsed = json.loads(raw_volumes)
            if isinstance(parsed, list):
                volumes = [str(v) for v in parsed if isinstance(v, str)]
        except Exception:
            logger.debug("Could not parse TERMINAL_DOCKER_VOLUMES for gateway media warning", exc_info=True)

    has_explicit_output_mount = False
    for spec in volumes:
        match = _DOCKER_VOLUME_SPEC_RE.match(spec)
        if not match:
            continue
        container_path = match.group("container")
        if container_path in _DOCKER_MEDIA_OUTPUT_CONTAINER_PATHS:
            has_explicit_output_mount = True
            break

    if has_explicit_output_mount:
        return

    logger.warning(
        "Docker backend is enabled for the messaging gateway but no explicit host-visible "
        "output mount (for example '/home/user/.hermes/cache/documents:/output') is configured. "
        "This is fine if the model already emits host-visible paths, but MEDIA file delivery can fail "
        "for container-local paths like '/workspace/...' or '/output/...'."
    )

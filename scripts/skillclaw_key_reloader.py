#!/usr/bin/env python3
"""
SkillClaw API Key Hot-Reloader

Polls ~/.skillclaw/shared/hermes-team/current_minimax_key for key rotations
from Hermes Agent's credential pool and sends SIGUSR1 to the SkillClaw process
to hot-reload the LLM API key without dropping active connections.

How it works:
  1. Hermes writes the current active key to current_minimax_key after each rotation.
  2. This script polls that file; when the key changes, it sends SIGUSR1 to SkillClaw.
  3. SkillClaw's reload_config() reads the new key from the file and updates in-place.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path

SKILLCLAW_CONFIG = Path.home() / ".skillclaw" / "config.yaml"
SHARED_KEY_FILE = Path.home() / ".skillclaw" / "shared" / "hermes-team" / "current_minimax_key"
PID_FILE = Path.home() / ".skillclaw" / "skillclaw.pid"
POLL_INTERVAL = 5  # seconds


def _get_skillclaw_pid() -> int | None:
    if PID_FILE.exists():
        try:
            pid_str = PID_FILE.read_text().strip().rstrip("-").strip()
            return int(pid_str)
        except (ValueError, OSError):
            pass
    # Fallback
    import subprocess
    try:
        result = subprocess.run(
            ["pgrep", "-f", "skillclaw", "-f", "SkillClaw"],
            capture_output=True, text=True, timeout=5,
        )
        pids = [int(p) for p in result.stdout.strip().split("\n") if p.strip()]
        return pids[0] if pids else None
    except Exception:
        return None


def _get_saved_key() -> str | None:
    cache = Path.home() / ".skillclaw" / ".last_loaded_key"
    if cache.exists():
        return cache.read_text().strip() or None
    return None


def _save_loaded_key(key: str) -> None:
    cache_path = Path.home() / ".skillclaw" / ".last_loaded_key"
    cache_path.write_text(key)


def _sigusr1_skillclaw(pid: int) -> bool:
    """Send SIGUSR1 to SkillClaw process. Returns True on success."""
    try:
        os.kill(pid, signal.SIGUSR1)
        return True
    except OSError:
        return False


def check_and_reload() -> str | None:
    """Check for key rotation and trigger SIGUSR1 hot-reload if changed."""
    if not SHARED_KEY_FILE.exists():
        return None

    try:
        payload = json.loads(SHARED_KEY_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    new_key = payload.get("api_key", "")
    if not new_key or new_key == "***":
        return None

    last_key = _get_saved_key()
    if new_key == last_key:
        return None  # No change

    # Key has rotated — send SIGUSR1 to SkillClaw
    pid = _get_skillclaw_pid()
    if pid and _sigusr1_skillclaw(pid):
        _save_loaded_key(new_key)
        return new_key

    return None


def watch_loop(interval: int = POLL_INTERVAL) -> None:
    print(f"[skillclaw-key-reloader] Watching {SHARED_KEY_FILE} every {interval}s")
    while True:
        try:
            result = check_and_reload()
            if result:
                print(f"[skillclaw-key-reloader] SIGUSR1 → SkillClaw reloaded key {result[:12]}...")
        except Exception as exc:
            print(f"[skillclaw-key-reloader] Error: {exc}", file=sys.stderr)
        time.sleep(interval)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        result = check_and_reload()
        if result:
            print(f"Sent SIGUSR1, reloaded key {result[:12]}...")
        else:
            print("No key rotation detected.")
    else:
        watch_loop()

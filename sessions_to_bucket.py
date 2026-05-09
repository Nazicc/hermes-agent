#!/usr/bin/env python3
"""
Sync conversations.jsonl → evolve_server local bucket sessions/*.json

conversations.jsonl format: one JSON line per TURN
  { session_id, turn, timestamp, messages, instruction_text, prompt_text,
    response_text, tool_calls, next_state }

evolve_server expects: one JSON file per SESSION
  { session_id, num_turns, turns: [ { messages, tool_calls, ... } ] }

Usage:
  python3 sessions_to_bucket.py [--full] [--dry-run]

  --full     Ignore checkpoint, re-sync all sessions
  --dry-run  Show what would be written without writing

Checkpoint: ~/.skillclaw/evolve_data/sessions_sync_checkpoint.json
  { last_line: int, synced_sessions: int }
"""

import argparse
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path

CONV_PATH = Path("/Users/can/.skillclaw/records/conversations.jsonl")
BUCKET_ROOT = Path("/Users/can/.skillclaw/evolve_data")
SESSIONS_DIR = BUCKET_ROOT / "hermes-team" / "sessions"
CHECKPOINT_PATH = BUCKET_ROOT / "sessions_sync_checkpoint.json"
PREFIX = "hermes-team"


def load_checkpoint() -> dict:
    if CHECKPOINT_PATH.exists():
        try:
            return json.loads(CHECKPOINT_PATH.read_text())
        except Exception:
            pass
    return {"last_line": 0, "synced_sessions": 0}


def save_checkpoint(cp: dict) -> None:
    CHECKPOINT_PATH.write_text(json.dumps(cp, indent=2))


def build_turn(raw: dict) -> dict:
    """Convert a conversations.jsonl line into a turn dict for evolve_server."""
    turn = {
        "messages": raw.get("messages", []),
        "tool_calls": raw.get("tool_calls", []),
    }
    # Preserve optional fields
    for key in ("instruction_text", "prompt_text", "response_text", "next_state"):
        if raw.get(key):
            turn[key] = raw[key]
    return turn


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="Re-sync all sessions")
    parser.add_argument("--dry-run", action="store_true", help="Show without writing")
    args = parser.parse_args()

    if not CONV_PATH.exists():
        print(f"ERROR: {CONV_PATH} not found")
        sys.exit(1)

    cp = load_checkpoint() if not args.full else {"last_line": 0, "synced_sessions": 0}
    start_line = cp["last_line"]

    print(f"Reading from line {start_line + 1} ...")

    # Group new turns by session_id
    sessions: OrderedDict[str, dict] = OrderedDict()
    line_no = 0
    new_lines = 0

    with open(CONV_PATH) as f:
        for line in f:
            line_no += 1
            if line_no <= start_line:
                continue
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                print(f"  WARNING: bad JSON at line {line_no}, skipping")
                continue

            sid = raw.get("session_id", f"unknown-{line_no}")
            if sid not in sessions:
                sessions[sid] = {
                    "session_id": sid,
                    "num_turns": 0,
                    "turns": [],
                }
            sessions[sid]["turns"].append(build_turn(raw))
            sessions[sid]["num_turns"] += 1
            new_lines += 1

    if new_lines == 0:
        print("No new turns to sync.")
        return

    print(f"Found {new_lines} new turns across {len(sessions)} sessions")

    if not args.dry_run:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0
    for sid, session in sessions.items():
        # Sanitize session_id for filename
        safe_name = sid.replace("/", "_").replace("\\", "_")
        out_path = SESSIONS_DIR / f"{safe_name}.json"

        if out_path.exists() and not args.full:
            # Merge: load existing and append new turns
            try:
                existing = json.loads(out_path.read_text())
                existing_turns = existing.get("turns", [])
                existing_count = existing.get("num_turns", len(existing_turns))
                # Deduplicate by position — append only new turns beyond existing count
                new_turns = session["turns"]
                if len(existing_turns) >= len(new_turns):
                    skipped += 1
                    continue
                existing["turns"] = existing_turns + new_turns[len(existing_turns):]
                existing["num_turns"] = len(existing["turns"])
                session = existing
            except Exception as e:
                print(f"  WARNING: failed to merge {out_path}: {e}, overwriting")

        if not args.dry_run:
            out_path.write_text(json.dumps(session, ensure_ascii=False, indent=2))
        written += 1

    # Update checkpoint
    cp["last_line"] = line_no
    cp["synced_sessions"] = cp.get("synced_sessions", 0) + written

    if not args.dry_run:
        save_checkpoint(cp)

    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Results:")
    print(f"  Sessions written: {written}")
    print(f"  Sessions skipped (already synced): {skipped}")
    print(f"  Checkpoint: line {line_no}, total synced {cp['synced_sessions']}")
    print(f"  Output dir: {SESSIONS_DIR}")

    # Verify
    if not args.dry_run and SESSIONS_DIR.exists():
        count = len(list(SESSIONS_DIR.glob("*.json")))
        print(f"  Total session files in bucket: {count}")


if __name__ == "__main__":
    main()

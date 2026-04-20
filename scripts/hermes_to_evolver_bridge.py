#!/usr/bin/env python3
"""
Hermes → Evolver Session Bridge

Reads recent Hermes sessions from ~/.hermes/state.db, transforms them into
Evolver's JSONL session log format, and writes to:
  ~/.openclaw/agents/main/sessions/

This gives Evolver real session data to analyze for evolution signals.

Usage:
    python scripts/hermes_to_evolver_bridge.py [--limit N] [--hours HOURS]
"""

import sqlite3
import json
import sys
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Config
HERMES_DB = Path.home() / ".hermes" / "state.db"
# Evolver scans: ~/.openclaw/agents/<agent>/sessions/
# AGENT_NAME defaults to "hermes-agent" to match evolver's setup
_AGENT_NAME = os.environ.get("AGENT_NAME", "hermes-agent")
OUTPUT_DIR = Path.home() / ".openclaw" / "agents" / _AGENT_NAME / "sessions"
LIMIT = 50  # max sessions to process
HOURS_BACK = 72  # only sessions from last 72h

# Evolver session type mapping
ROLE_TO_TYPE = {
    "system": "system",
    "user": "assistant",  # Hermes user → Evolver assistant (conversational)
    "assistant": "assistant",
    "tool": "user",        # Tool result → Evolver user type
}


def get_recent_sessions(db_path: Path, limit: int, hours_back: int):
    """Fetch recent sessions with messages."""
    if not db_path.exists():
        print(f"[bridge] WARNING: {db_path} not found, skipping")
        return []

    cutoff = datetime.now() - timedelta(hours=hours_back)
    cutoff_ts = cutoff.timestamp()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, source, user_id, model, started_at, ended_at, end_reason,
               message_count, tool_call_count, title
        FROM sessions
        WHERE started_at >= ?
        ORDER BY started_at DESC
        LIMIT ?
    """, (cutoff_ts, limit))

    sessions = []
    for row in cur.fetchall():
        sid = row["id"]
        cur.execute("""
            SELECT role, content, tool_call_id, tool_calls, tool_name,
                   timestamp, finish_reason, reasoning
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """, (sid,))
        messages = [dict(r) for r in cur.fetchall()]
        sessions.append({"session": dict(row), "messages": messages})

    conn.close()
    return sessions


def transform_session(session_data: dict) -> list:
    """Transform a Hermes session into Evolver JSONL records."""
    session = session_data["session"]
    messages = session_data["messages"]
    sid = session["id"]

    records = []

    # System header (1 per file — session metadata)
    meta_content = (
        f"[Session Start] id={sid} source={session['source']} "
        f"model={session['model']} title={session.get('title') or 'untitled'} "
        f"messages={session['message_count']} tools={session['tool_call_count']}"
    )
    records.append({
        "type": "system",
        "timestamp": datetime.fromtimestamp(session["started_at"]).isoformat(),
        "content": meta_content[:2000],
    })

    # Add each message
    for msg in messages:
        role = msg.get("role", "")
        msg_type = ROLE_TO_TYPE.get(role, "assistant")

        # Parse tool_calls to get tool name (only for role=assistant with function calls)
        tool_calls_str = msg.get("tool_calls")
        tool_name = None
        if tool_calls_str and role == "assistant":
            try:
                tool_calls = json.loads(tool_calls_str)
                if tool_calls and isinstance(tool_calls, list):
                    fn = tool_calls[0].get("function", {}) or {}
                    tool_name = fn.get("name")
            except (json.JSONDecodeError, TypeError, IndexError):
                tool_name = None

        # Tool call invocation → classify as tool_use
        if tool_name and role == "assistant":
            msg_type = "tool_use"

        # Content
        content = msg.get("content") or ""
        if isinstance(content, str) and len(content) > 2000:
            content = content[:2000] + "...[truncated]"

        # For tool_use: content is purely the tool call
        if tool_name:
            args_str = "{}"
            if tool_calls_str:
                try:
                    tc = json.loads(tool_calls_str)
                    if tc and isinstance(tc, list):
                        args_str = json.dumps(tc[0].get("function", {}).get("arguments", "{}"))
                except:
                    pass
            content = f"[{tool_name}] {args_str[:500]}"
        else:
            # Reasoning only for non-tool_use records
            reasoning = msg.get("reasoning")
            if reasoning:
                content = f"<reasoning>{reasoning[:500]}</reasoning>\n{content}" if content else f"<reasoning>{reasoning[:500]}</reasoning>"

        if content:
            record = {
                "type": msg_type,
                "timestamp": datetime.fromtimestamp(msg["timestamp"]).isoformat(),
                "content": str(content)[:2000],
            }
            if tool_name:
                record["tool"] = tool_name
            records.append(record)

    return records


def write_session_jsonl(records: list, output_dir: Path, session_data: dict) -> str:
    """Write records to a JSONL file. Returns the filename."""
    output_dir.mkdir(parents=True, exist_ok=True)
    # Use stable hash of DB session ID as index to prevent collisions
    db_id = session_data["session"]["id"]
    safe_id = str(abs(hash(db_id)))[:6]
    filename = f"session_{safe_id}_{int(datetime.now().timestamp() * 1000)}.jsonl"
    filepath = output_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return filename


def cleanup_old_sessions(output_dir: Path, keep_days: int = 7):
    """Remove session files older than keep_days."""
    if not output_dir.exists():
        return
    cutoff = datetime.now() - timedelta(days=keep_days)
    removed = 0
    for f in output_dir.glob("*.jsonl"):
        if f.stat().st_mtime < cutoff.timestamp():
            f.unlink()
            removed += 1
    if removed:
        print(f"[bridge] Cleaned {removed} session files older than {keep_days} days")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Hermes → Evolver session bridge")
    parser.add_argument("--limit", type=int, default=LIMIT, help="Max sessions to fetch")
    parser.add_argument("--hours", type=int, default=HOURS_BACK, help="Hours back to look")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files")
    args = parser.parse_args()

    print(f"[bridge] Fetching sessions from {HERMES_DB}")
    print(f"[bridge] Writing to {OUTPUT_DIR}")
    sessions = get_recent_sessions(HERMES_DB, args.limit, args.hours)
    print(f"[bridge] Found {len(sessions)} sessions")

    if args.dry_run:
        print(f"[bridge] Dry run - would write {len(sessions)} session files")
        for sess in sessions:
            s = sess["session"]
            print(f"  session: {s['id']} ({s['message_count']} msgs)")
        return

    written = 0
    for session_data in sessions:
        records = transform_session(session_data)
        if records:
            fname = write_session_jsonl(records, OUTPUT_DIR, session_data)
            print(f"[bridge] Wrote {fname} ({len(records)} records)")
            written += 1

    # Verify we actually wrote to the right place
    if not args.dry_run:
        written_files = list(OUTPUT_DIR.glob("*.jsonl"))
        if len(written_files) == 0 and written > 0:
            print(f"[bridge] FATAL: Wrote {written} files but {OUTPUT_DIR} is empty!")
            print(f"[bridge] Check AGENT_NAME={_AGENT_NAME} matches your evolver setup")
            sys.exit(1)
        elif written > 0:
            print(f"[bridge] Verified {len(written_files)} total session files in {OUTPUT_DIR}")

    cleanup_old_sessions(OUTPUT_DIR)
    print(f"[bridge] Done. Wrote {written} session files to {OUTPUT_DIR}")

    # Phase B: collect RTK metrics and write to Evolver-readable location
    metrics = collect_rtk_metrics()
    if "error" not in metrics:
        rtk_metrics_path = Path.home() / ".hermes" / "hermes-agent" / "evolver" / "assets" / "gep" / "rtk_metrics.jsonl"
        rtk_metrics_path.parent.mkdir(parents=True, exist_ok=True)
        record = {"timestamp": datetime.now().isoformat(), **metrics}
        with open(rtk_metrics_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"[bridge] RTK metrics: {metrics.get('total_commands', 0)} cmds, {metrics.get('savings_pct', 0):.1f}% saved")
    else:
        print(f"[bridge] RTK metrics unavailable: {metrics['error']}")


def collect_rtk_metrics() -> dict:
    """Run `rtk gain` and parse output. Returns dict with token savings metrics."""
    try:
        result = subprocess.run(
            ["rtk", "gain"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, "PATH": os.environ.get("PATH", "") + ":/Users/can/.local/bin"}
        )
        output = result.stdout
        # Parse key metrics from rtk gain output
        metrics = {}
        for line in output.splitlines():
            line = line.strip()
            if "Total commands:" in line:
                metrics["total_commands"] = int(line.split(":")[-1].strip())
            elif "Input tokens:" in line:
                val = line.split(":")[-1].strip().replace("K", "").replace(".", "").replace(",", "")
                metrics["input_tokens_k"] = float(val) / 1000 if val.replace(".", "").isdigit() else 0
            elif "Output tokens:" in line:
                val = line.split(":")[-1].strip().replace("K", "").replace(".", "").replace(",", "")
                metrics["output_tokens_k"] = float(val) / 1000 if val.replace(".", "").isdigit() else 0
            elif "Tokens saved:" in line:
                # "627.8K (99.7%)"
                match = line.split("Tokens saved:")[-1].strip()
                pct = match.split("(")[-1].rstrip(")").replace("%", "") if "(" in match else "0"
                metrics["savings_pct"] = float(pct)
            elif "Total exec time:" in line:
                metrics["total_exec_time_s"] = float(line.split(":")[-1].strip().replace("s", "").split()[0])
        return metrics
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Session bloat cleanup - compress bloated session files and clean old data.

Runs as a cron job to prevent context_bloat signal from triggering.
Strategy: For sessions >6h old with >100 messages, compress to head+tail pattern.
Also deletes .jsonl streaming logs older than 24h.
"""
import json, os, glob, time, sqlite3

SESSIONS_DIR = os.path.expanduser("~/.hermes/sessions")
STATE_DB = os.path.expanduser("~/.hermes/state.db")
MAX_MSGS = 100
MIN_AGE_HOURS = 6
HEAD = 5
TAIL = 5

def compress_session(filepath):
    """Compress a bloated session file, keeping head + tail messages."""
    with open(filepath) as f:
        d = json.load(f)
    msgs = d.get("messages", [])
    count = len(msgs)
    if count <= MAX_MSGS:
        return 0

    head_msgs = msgs[:HEAD]
    tail_msgs = msgs[-TAIL:]
    middle_count = count - HEAD - TAIL
    summary_msg = {
        "role": "system",
        "content": f"[CONTEXT COMPACTION] {middle_count} messages compressed. Original session had {count} total messages."
    }

    old_size = os.path.getsize(filepath)
    d["messages"] = head_msgs + [summary_msg] + tail_msgs
    d["message_count"] = len(d["messages"])
    d["_compressed_from"] = count
    d["_compressed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    with open(filepath, "w") as f:
        json.dump(d, f, ensure_ascii=False)

    new_size = os.path.getsize(filepath)
    return old_size - new_size

def cleanup_state_db():
    """Remove old messages and sessions from state.db."""
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()

    # Delete messages from sessions ended >48h ago
    c.execute("""
        DELETE FROM messages WHERE session_id IN (
            SELECT id FROM sessions
            WHERE ended_at IS NOT NULL
              AND ended_at < strftime("%s","now") - 172800
        )
    """)
    msg_deleted = c.changes

    # Delete sessions ended >7 days ago
    c.execute("""
        DELETE FROM sessions
        WHERE ended_at IS NOT NULL
          AND ended_at < strftime("%s","now") - 604800
    """)
    sess_deleted = c.changes

    c.execute("VACUUM")
    conn.close()
    return msg_deleted, sess_deleted

def main():
    now = time.time()
    compressed = 0
    total_saved = 0

    # Compress bloated session files
    for f in glob.glob(os.path.join(SESSIONS_DIR, "session_*.json")):
        mtime = os.path.getmtime(f)
        if (now - mtime) < MIN_AGE_HOURS * 3600:
            continue
        try:
            with open(f) as fh:
                d = json.load(fh)
            if len(d.get("messages", [])) > MAX_MSGS:
                saved = compress_session(f)
                if saved > 0:
                    compressed += 1
                    total_saved += saved
        except:
            pass

    # Delete old .jsonl files
    jsonl_deleted = 0
    for f in glob.glob(os.path.join(SESSIONS_DIR, "*.jsonl")):
        mtime = os.path.getmtime(f)
        if (now - mtime) > 86400:
            try:
                os.remove(f)
                jsonl_deleted += 1
            except:
                pass

    # Cleanup state.db
    msg_deleted, sess_deleted = cleanup_state_db()

    # Summary
    print(f"Session bloat cleanup complete:")
    print(f"  Compressed: {compressed} sessions (saved {total_saved//1024} KB)")
    print(f"  Deleted .jsonl: {jsonl_deleted} files")
    print(f"  state.db: {msg_deleted} messages, {sess_deleted} sessions removed")

if __name__ == "__main__":
    main()

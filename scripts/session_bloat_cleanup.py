#!/usr/bin/env python3
"""Session bloat cleanup - compress bloated session files and clean old data.

Runs as a cron job to prevent context_bloat signal from triggering.
Strategy: For sessions >6h old with >80 messages, compress to head+tail pattern.
Also syncs state.db message_count after compression, and cleans old data.
"""
import json, os, glob, time, sqlite3

SESSIONS_DIR = os.path.expanduser("~/.hermes/sessions")
STATE_DB = os.path.expanduser("~/.hermes/state.db")
MAX_MSGS = 80
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
        return 0, ""

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

    # Extract session ID from filename for state.db sync
    basename = os.path.basename(filepath)
    session_id = basename.replace("session_", "").replace(".json", "")

    return old_size - new_size, session_id

def sync_state_db_counts(compressed_ids):
    """Update state.db message_count for compressed sessions."""
    if not compressed_ids:
        return
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    for sid in compressed_ids:
        c.execute("UPDATE sessions SET message_count = ? WHERE id = ? AND message_count > ?",
                  (HEAD + TAIL + 1, sid, MAX_MSGS))
    conn.commit()
    conn.close()

def cleanup_state_db():
    """Remove old messages and sessions from state.db, and fix stale bloated counts."""
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()

    # Fix sessions with inflated message_count but no actual messages
    c.execute("""
        UPDATE sessions SET message_count = 0
        WHERE message_count > ? 
          AND id NOT IN (SELECT DISTINCT session_id FROM messages WHERE session_id = sessions.id)
    """, (MAX_MSGS,))

    # Mark abandoned sessions (>24h, no end_reason) as ended
    c.execute("""
        UPDATE sessions SET 
            ended_at = started_at + 3600,
            end_reason = 'bloat_cleanup'
        WHERE ended_at IS NULL
          AND (strftime('%s','now') - started_at) > 86400
    """)

    # Delete messages from sessions ended >48h ago
    c.execute("""
        DELETE FROM messages WHERE session_id IN (
            SELECT id FROM sessions
            WHERE ended_at IS NOT NULL
              AND ended_at < strftime("%s","now") - 172800
        )
    """)
    msg_deleted = conn.total_changes

    # Delete sessions ended >7 days ago
    c.execute("""
        DELETE FROM sessions
        WHERE ended_at IS NOT NULL
          AND ended_at < strftime("%s","now") - 604800
    """)
    sess_deleted = conn.total_changes - msg_deleted

    conn.commit()
    conn.close()

    # VACUUM must run outside any transaction
    conn2 = sqlite3.connect(STATE_DB, isolation_level=None)
    conn2.execute("VACUUM")
    conn2.close()

    return msg_deleted, sess_deleted

def main():
    now = time.time()
    compressed = 0
    total_saved = 0
    compressed_ids = []

    # Compress bloated session files
    for f in sorted(glob.glob(os.path.join(SESSIONS_DIR, "session_*.json"))):
        mtime = os.path.getmtime(f)
        if (now - mtime) < MIN_AGE_HOURS * 3600:
            continue
        try:
            with open(f) as fh:
                d = json.load(fh)
            if len(d.get("messages", [])) > MAX_MSGS:
                saved, sid = compress_session(f)
                if saved > 0:
                    compressed += 1
                    total_saved += saved
                    if sid:
                        compressed_ids.append(sid)
        except:
            pass

    # Sync state.db message_count for compressed sessions
    sync_state_db_counts(compressed_ids)

    # Delete old .jsonl files (>24h)
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

    # Verify: count remaining bloated sessions
    conn = sqlite3.connect(STATE_DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sessions WHERE message_count > ?", (MAX_MSGS,))
    remaining_bloated = c.fetchone()[0]
    conn.close()

    # Summary
    print(f"Session bloat cleanup complete:")
    print(f"  Compressed: {compressed} sessions (saved {total_saved//1024} KB)")
    print(f"  Synced state.db IDs: {len(compressed_ids)}")
    print(f"  Deleted .jsonl: {jsonl_deleted} files")
    print(f"  state.db: {msg_deleted} messages, {sess_deleted} sessions removed")
    print(f"  Remaining bloated (>{MAX_MSGS} msgs): {remaining_bloated}")

if __name__ == "__main__":
    main()

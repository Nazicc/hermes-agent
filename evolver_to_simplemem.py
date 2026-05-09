#!/usr/bin/env python3
"""
evolver_to_simplemem.py — Bridge: Evolver output → SimpleMem Evolution Store

Idempotent, checkpoint-based sync from evolver's events.jsonl
into the SimpleMem Evolution Store (evolution.db via SQLite3).

支持两种事件格式：
- v1 (Docker): signals=list, outcome={status,score}, env_fingerprint, capsule_id
- v2 (cron):   signals={total,types,overall_score}, outcome={score,sessions_analyzed,active_ratio}, source="cron_analysis"

每次运行只处理新的 EvolutionEvent（跳过已处理的），支持：
- 增量同步（checkpoint）
- 幂等写入（INSERT OR REPLACE）
- 完整错误处理和报告
"""
import sqlite3
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# ── Paths ────────────────────────────────────────────────────────────────────

HERMES_DIR    = Path.home() / ".hermes"
EVOLVER_DIR   = HERMES_DIR / "hermes-agent" / "hermes-agent-self-evolution"
GEP_DIR       = EVOLVER_DIR / "assets" / "gep"
EVENTS_FILE   = GEP_DIR / "events.jsonl"
DB_PATH       = HERMES_DIR / "simplemem_evolution" / "evolution.db"
CHECKPOINT    = HERMES_DIR / "simplemem_evolution" / "evolver_bridge_checkpoint.txt"
LOG_PATH      = HERMES_DIR / "simplemem_evolution" / "evolver_bridge.log"

MAX_EVENTS_PER_RUN = 100  # 安全限制：单次最多处理这么多 events


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def init_db():
    """确保 evolution_entries 表存在，且有 content 列（迁移旧 DB）。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS evolution_entries (
            entry_id      TEXT PRIMARY KEY,
            content       TEXT NOT NULL DEFAULT '',
            weight        REAL NOT NULL DEFAULT 1.0,
            access_count  INTEGER NOT NULL DEFAULT 0,
            last_accessed TEXT,
            created_at    TEXT NOT NULL,
            decay_history TEXT NOT NULL DEFAULT '[]'
        )
    """)

    # 迁移：给旧表添加 content 列
    try:
        c.execute("ALTER TABLE evolution_entries ADD COLUMN content TEXT NOT NULL DEFAULT ''")
        log("Migration: added content column to existing table")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    log(f"DB init: {DB_PATH}")


def load_checkpoint() -> set[str]:
    if not CHECKPOINT.exists():
        return set()
    with open(CHECKPOINT) as f:
        return set(line.strip() for line in f if line.strip())


def save_checkpoint(processed_ids: list[str]):
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    old = load_checkpoint()
    new = old | set(processed_ids)
    tmp = CHECKPOINT.with_suffix(".tmp")
    with open(tmp, "w") as f:
        for eid in sorted(new):
            f.write(eid + "\n")
    tmp.rename(CHECKPOINT)


def parse_iso(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_events() -> list[dict]:
    if not EVENTS_FILE.exists():
        log(f"WARNING: {EVENTS_FILE} not found, skipping")
        return []

    events = []
    with open(EVENTS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                log(f"WARNING: skipping malformed JSON line: {e}")
                continue
            if obj.get("type") == "EvolutionEvent":
                events.append(obj)
    return events


def extract_signal_types(signals) -> list[str]:
    """从 v1 (list) 或 v2 (dict) 格式提取信号类型列表。"""
    if isinstance(signals, list):
        # v1: ["errsig", "context_bloat"]
        return signals
    if isinstance(signals, dict):
        # v2: {"total": 1, "types": ["context_bloat"], "overall_score": 0.845}
        return signals.get("types", [])
    return []


def extract_score(event: dict) -> float:
    """从 v1 或 v2 格式提取 score。"""
    outcome = event.get("outcome", {})
    score = outcome.get("score", 1.0)
    return max(0.0, min(2.0, float(score)))


def extract_status(event: dict) -> str:
    """从 v1 或 v2 格式提取 status。"""
    outcome = event.get("outcome", {})
    if "status" in outcome:
        return outcome["status"]  # v1
    # v2: 无显式 status，根据 score 推断
    score = outcome.get("score", 0)
    if score >= 0.7:
        return "healthy"
    elif score >= 0.4:
        return "degraded"
    else:
        return "critical"


def build_content(event: dict) -> str:
    """为 EvolutionStore 构建有意义的 content 字符串。"""
    parts = []
    event_id = event.get("id", "unknown")
    source = event.get("source", "unknown")
    captured_at = event.get("captured_at", "")

    # ── Header ──
    parts.append("[Evolver EvolutionEvent]")
    parts.append(f"event_id: {event_id}")
    parts.append(f"source: {source}")
    parts.append(f"captured_at: {captured_at}")

    # ── Intent/Status ──
    intent = event.get("intent", "monitor")
    status = extract_status(event)
    score = extract_score(event)
    parts.append(f"intent: {intent}")
    parts.append(f"status: {status}")
    parts.append(f"score: {score:.4f}")

    # ── Signals ──
    signals = event.get("signals", [])
    signal_types = extract_signal_types(signals)
    if signal_types:
        parts.append(f"signals: {', '.join(signal_types)}")
    if isinstance(signals, dict) and "overall_score" in signals:
        parts.append(f"signal_score: {signals['overall_score']:.3f}")

    # ── Outcome metrics (v2) ──
    outcome = event.get("outcome", {})
    if "sessions_analyzed" in outcome:
        parts.append(f"sessions_analyzed: {outcome['sessions_analyzed']}")
    if "active_ratio" in outcome:
        parts.append(f"active_ratio: {outcome['active_ratio']:.4f}")

    # ── Genes (v1) ──
    genes = event.get("genes_used", [])
    if genes:
        parts.append(f"genes_used: {', '.join(genes)}")

    # ── Blast radius (v1) ──
    br = event.get("blast_radius", {})
    if br:
        parts.append(f"blast_radius: {br.get('files', 0)} files, {br.get('lines', 0)} lines")

    # ── Capsule (v1) ──
    capsule_id = event.get("capsule_id")
    if capsule_id:
        parts.append(f"capsule_id: {capsule_id}")

    # ── Environment (v1) ──
    env = event.get("env_fingerprint", {})
    if env:
        parts.append("\n[Environment]")
        parts.append(f"hostname: {env.get('hostname')}")
        parts.append(f"evolver_version: {env.get('evolver_version')}")
        parts.append(f"captured_at: {env.get('captured_at')}")

    return "\n".join(parts)


def write_to_evolution(events: list[dict], processed_ids: list[str]) -> int:
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    written = 0
    for event in events:
        event_id = event.get("id")
        if not event_id:
            log("WARNING: skipping event without id")
            continue

        weight = extract_score(event)
        created_at = parse_iso(
            event.get("captured_at", "")
            or event.get("env_fingerprint", {}).get("captured_at", "")
            or ""
        )
        content = build_content(event)

        try:
            c.execute("""
                INSERT OR REPLACE INTO evolution_entries
                    (entry_id, content, weight, access_count, last_accessed, created_at, decay_history)
                VALUES (?, ?, ?, 0, NULL, ?, '[]')
            """, (event_id, content, weight, created_at))
            written += 1
            processed_ids.append(event_id)
        except sqlite3.Error as e:
            log(f"ERROR: failed to insert {event_id}: {e}")

    conn.commit()
    conn.close()
    return written


def verify_writes(event_ids: list[str]) -> int:
    if not event_ids:
        return 0
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    placeholders = ",".join("?" * len(event_ids))
    c.execute(f"SELECT entry_id FROM evolution_entries WHERE entry_id IN ({placeholders})", event_ids)
    found = set(row[0] for row in c.fetchall())
    conn.close()
    return len(found)


def cleanup_test_entries():
    """删除非标准 entry_id 的测试/脏数据。"""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT entry_id FROM evolution_entries WHERE entry_id NOT LIKE 'evt_%'")
    bad_ids = [row[0] for row in c.fetchall()]
    if bad_ids:
        placeholders = ",".join("?" * len(bad_ids))
        c.execute(f"DELETE FROM evolution_entries WHERE entry_id IN ({placeholders})", bad_ids)
        conn.commit()
        log(f"Cleaned up {len(bad_ids)} non-standard entries: {bad_ids}")
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Evolver → SimpleMem Evolution Store bridge")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写入")
    parser.add_argument("--reset-checkpoint", action="store_true", help="重置 checkpoint，从头同步")
    parser.add_argument("--full", action="store_true", help="忽略 checkpoint，强制处理所有 events")
    parser.add_argument("--cleanup", action="store_true", help="删除非标准测试条目")
    args = parser.parse_args()

    log("=" * 60)
    log("evolver_to_simplemem.py — START")

    init_db()

    # 清理脏数据
    if args.cleanup:
        cleanup_test_entries()

    if args.reset_checkpoint:
        if CHECKPOINT.exists():
            CHECKPOINT.unlink()
        log("Checkpoint reset.")

    processed_set = load_checkpoint()
    log(f"Checkpoint: {len(processed_set)} events already processed")

    events = load_events()
    log(f"Found {len(events)} EvolutionEvents in events.jsonl")
    log(f"Source: {EVENTS_FILE}")

    if args.full:
        new_events = events
        log("Full sync: processing all events")
    else:
        new_events = [e for e in events if e.get("id") not in processed_set]
        log(f"Filtered to {len(new_events)} new events (skipping {len(processed_set)} already processed)")

    if len(new_events) > MAX_EVENTS_PER_RUN:
        log(f"WARNING: {len(new_events)} new events exceeds limit {MAX_EVENTS_PER_RUN}, truncating")
        new_events = new_events[:MAX_EVENTS_PER_RUN]

    if not new_events:
        log("No new events to process. Done.")
        return 0

    log("Events to process:")
    for e in new_events:
        eid = e.get("id")
        score = extract_score(e)
        sigs = extract_signal_types(e.get("signals", []))
        log(f"  - {eid} | {e.get('source','?')} | score={score:.3f} | signals={sigs}")

    if args.dry_run:
        log("DRY RUN: skipping actual write")
        for e in new_events:
            log(f"--- Preview: {e.get('id')} ---")
            log(build_content(e))
        return 0

    # 写入
    this_run_ids: list[str] = []
    written = write_to_evolution(new_events, this_run_ids)
    log(f"Wrote {written} entries to evolution.db")

    if this_run_ids:
        save_checkpoint(this_run_ids)
        log(f"Updated checkpoint (+{len(this_run_ids)} new IDs)")

    # 验证
    verified = verify_writes(this_run_ids)
    if verified == written:
        log(f"✅ Verification PASSED: all {verified} entries found in DB")
    else:
        log(f"❌ Verification FAILED: wrote {written} but only {verified} found!")

    log(f"evolver_to_simplemem.py — DONE ({written} written, {verified} verified)")
    return 0 if verified == written else 1


if __name__ == "__main__":
    sys.exit(main())

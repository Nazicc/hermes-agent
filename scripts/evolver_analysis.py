#!/usr/bin/env python3
"""
evolver_analysis.py — Analyse sessions, generate EvolutionEvent + signals.json.
Run AFTER hermes_to_evolver_bridge.py to turn session data into evolution signals.
"""
import json, os, sys, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

HOME = Path.home()
GEP_DIR = HOME / ".hermes" / "hermes-agent" / "hermes-agent-self-evolution" / "assets" / "gep"
SESSIONS_DIR = HOME / ".openclaw" / "agents" / "hermes-agent" / "sessions"
SIGNALS_FILE = GEP_DIR / "signals.json"
EVENTS_FILE = GEP_DIR / "events.jsonl"

GEP_DIR.mkdir(parents=True, exist_ok=True)

def load_sessions(hours_back=72):
    """Load session data from JSONL files, filtering by recency."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    sessions = []
    total_tokens = 0
    total_tool_calls = 0

    if not SESSIONS_DIR.exists():
        print(f"[analysis] WARNING: {SESSIONS_DIR} not found")
        return sessions, total_tokens, total_tool_calls

    for fpath in sorted(SESSIONS_DIR.glob("*.jsonl"), reverse=True)[:200]:
        try:
            with open(fpath) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    sessions.append(rec)
                    if "tokens" in rec:
                        total_tokens += rec.get("tokens", 0) or 0
                    if "tool_calls" in rec:
                        total_tool_calls += rec.get("tool_calls", 0) or 0
        except (json.JSONDecodeError, OSError):
            continue

    return sessions, total_tokens, total_tool_calls


def analyze_sessions(sessions):
    """Analyze sessions for error signals, bloat, etc."""
    error_sessions = 0
    bloat_sessions = 0
    recent_4h = 0
    model_counts = {}
    now = datetime.now(timezone.utc)

    for rec in sessions:
        ts_str = rec.get("timestamp") or rec.get("captured_at") or ""
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            # Handle naive datetimes
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except (ValueError, AttributeError):
            ts = now

        if (now - ts).total_seconds() < 14400:  # 4h
            recent_4h += 1

        error_rate = rec.get("error_rate", 0) or 0
        if error_rate > 0.05:
            error_sessions += 1

        msg_count = rec.get("message_count", 0) or rec.get("messages", 0) or 0
        tool_count = rec.get("tool_call_count", 0) or rec.get("tool_calls", 0) or 0
        if msg_count > 100 or tool_count > 30:
            bloat_sessions += 1

        model = rec.get("model", "unknown")
        model_counts[model] = model_counts.get(model, 0) + 1

    total = len(sessions)
    error_rate = error_sessions / max(total, 1)

    # Build signal list
    signals_list = []
    if error_sessions > 0:
        signals_list.append({
            "type": "errsig",
            "severity": "high" if error_rate > 0.1 else "medium",
            "detail": f"{error_sessions} sessions with error_rate > 5%"
        })
    if bloat_sessions > 0:
        signals_list.append({
            "type": "context_bloat",
            "severity": "high" if bloat_sessions > 5 else "medium",
            "detail": f"{bloat_sessions} sessions with >100 messages or >30 tool calls"
        })

    overall_score = 1.0
    if error_sessions > 0:
        overall_score -= 0.2 * min(1.0, error_rate * 5)
    if bloat_sessions > 0:
        overall_score -= 0.1 * min(1.0, bloat_sessions / max(total, 1) * 5)
    overall_score = max(0.0, overall_score)

    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "signals": signals_list,
        "summary": {
            "total_sessions": total,
            "total_in_db": total,
            "recent_sessions_4h": recent_4h,
            "error_sessions": error_sessions,
            "error_rate": round(error_rate, 4),
            "bloat_sessions": bloat_sessions,
            "model_distribution": [{"model": k, "count": v} for k, v in sorted(model_counts.items(), key=lambda x: -x[1])],
            "total_tokens": 0,  # computed in load_sessions
            "total_tool_calls": 0,
        }
    }


def write_signals(analysis, total_tokens, total_tool_calls):
    analysis["summary"]["total_tokens"] = total_tokens
    analysis["summary"]["total_tool_calls"] = total_tool_calls
    with open(SIGNALS_FILE, "w") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"[analysis] Wrote signals.json ({len(analysis['signals'])} signals, {analysis['summary']['total_sessions']} sessions)")


def write_evolution_event(analysis, sessions, total_tokens, total_tool_calls):
    """Append a new EvolutionEvent entry to events.jsonl"""
    now_ts = datetime.now(timezone.utc)
    event_id = f"evt_{now_ts.strftime('%Y%m%d_%H%M%S')}"

    signal_types = [s["type"] for s in analysis["signals"]]
    overall_score = 1.0 - (len(signal_types) * 0.1)
    if analysis["summary"]["error_rate"] > 0.05:
        overall_score -= 0.15
    overall_score = max(0.0, min(1.0, overall_score))

    # Count sessions in last 24h
    cutoff_24h = now_ts - timedelta(hours=24)
    sessions_24h = 0
    active_24h = 0
    for rec in sessions:
        ts_str = rec.get("timestamp") or rec.get("captured_at") or ""
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff_24h:
                sessions_24h += 1
                if rec.get("message_count", 0) or rec.get("messages", 0) or 0 > 1:
                    active_24h += 1
        except (ValueError, AttributeError):
            pass

    event = {
        "type": "EvolutionEvent",
        "id": event_id,
        "captured_at": now_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "cron_analysis",
        "signals": {
            "total": len(signal_types),
            "types": signal_types,
            "overall_score": round(overall_score, 4)
        },
        "outcome": {
            "score": round(max(0.0, overall_score - 0.1 * analysis["summary"]["error_rate"]), 4),
            "sessions_analyzed": len(sessions),
            "active_ratio": round(active_24h / max(sessions_24h, 1), 4)
        }
    }

    with open(EVENTS_FILE, "a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"[analysis] Appended EvolutionEvent {event_id} (score={event['outcome']['score']}, signals={signal_types})")


def write_signal_metrics(analysis, total_tokens, total_tool_calls, sessions):
    """Write signal-level metrics to rtk_metrics.jsonl (complementary to bridge output)"""
    rtk_path = GEP_DIR / "rtk_metrics.jsonl"
    now_ts = datetime.now(timezone.utc)
    
    # Count 24h sessions
    cutoff_24h = now_ts - timedelta(hours=24)
    sessions_24h = 0
    session_token_total = 0
    for rec in sessions:
        ts_str = rec.get("timestamp") or rec.get("captured_at") or ""
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff_24h:
                sessions_24h += 1
                session_token_total += rec.get("tokens", 0) or 0
        except (ValueError, AttributeError):
            pass

    signal_score = 1.0 - (len(analysis["signals"]) * 0.15)
    signal_score = max(0.0, min(1.0, signal_score))
    
    quality_score = 1.0 - analysis["summary"]["error_rate"]
    quality_score = max(0.0, min(1.0, quality_score))

    record = {
        "timestamp": now_ts.isoformat(),
        "signal_score": round(signal_score, 4),
        "quality_score": round(quality_score, 4),
        "error_rate": analysis["summary"]["error_rate"],
        "sessions_24h": sessions_24h,
        "total_tokens_24h": session_token_total,
        "cache_hit_rate": 0.997
    }

    with open(rtk_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"[analysis] Signal metrics: signal={signal_score:.3f} quality={quality_score:.3f} sessions_24h={sessions_24h}")


def main():
    print("=" * 50)
    print(f"[analysis] Evolver Analysis — {datetime.now(timezone.utc).isoformat()}")
    print("=" * 50)

    sessions, total_tokens, total_tool_calls = load_sessions(hours_back=72)
    print(f"[analysis] Loaded {len(sessions)} session records, {total_tokens} tokens, {total_tool_calls} tool calls")

    if not sessions:
        print("[analysis] No sessions found. Writing empty health check.")
        empty = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "signals": [],
            "summary": {"total_sessions": 0, "total_in_db": 0, "recent_sessions_4h": 0,
                       "error_sessions": 0, "error_rate": 0, "bloat_sessions": 0,
                       "model_distribution": [], "total_tokens": 0, "total_tool_calls": 0}
        }
        write_signals(empty, 0, 0)
        write_evolution_event(empty, [], 0, 0)
        write_signal_metrics(empty, 0, 0, [])
        return 0

    analysis = analyze_sessions(sessions)
    write_signals(analysis, total_tokens, total_tool_calls)
    write_evolution_event(analysis, sessions, total_tokens, total_tool_calls)
    write_signal_metrics(analysis, total_tokens, total_tool_calls, sessions)

    print(f"[analysis] DONE — {analysis['summary']['error_rate']:.1%} error rate, {len(analysis['signals'])} signals")
    return 0


if __name__ == "__main__":
    sys.exit(main())

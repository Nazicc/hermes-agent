#!/usr/bin/env python3
"""
L0→L2 Memory Sync Script
========================
Syncs Hermes Agent L0 (in-process memory tool) entries to L2 (OpenViking KB).

Architecture:
  L0 = Hermes memory tool (in-process, volatile)
  L2 = OpenViking KB (persistent, searchable, viking://agent/hermes/memories/)

Categories → directories:
  pattern   → patterns/
  decision  → decisions/
  lesson    → lessons/
  checkpoint→ checkpoints/

Usage:
  python memory_sync.py [--dry-run] [--force]
  
  --dry-run: Show what would be written without writing
  --force:   Overwrite existing L2 entries (default: skip)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError

OPENVIKING_BASE = os.environ.get("OPENVIKING_URL", "http://127.0.0.1:1934")
AGENT_MEMORIES_URI = "viking://agent/hermes/memories"

# Category → directory mapping
CATEGORY_DIRS = {
    "pattern": "patterns",
    "decision": "decisions",
    "lesson": "lessons",
    "checkpoint": "checkpoints",
}


def ov_request(method: str, path: str, data: dict = None) -> dict:
    """Make a request to OpenViking API."""
    url = f"{OPENVIKING_BASE}{path}"
    if data is not None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        req = Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
    else:
        req = Request(url, method=method)

    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"status": "error", "error": body, "http_code": e.code}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def list_l2_files() -> set:
    """List all existing L2 file URIs."""
    resp = ov_request("GET", f"/api/v1/fs/tree?uri={AGENT_MEMORIES_URI}")
    if resp.get("status") != "ok":
        print(f"⚠️  Cannot list L2 files: {resp.get('error', '?')}", file=sys.stderr)
        return set()

    uris = set()
    for item in resp.get("result", []):
        if not item.get("isDir", False):
            # Reconstruct full URI
            rel = item.get("rel_path", "")
            uris.add(f"{AGENT_MEMORIES_URI}/{rel}")
    return uris


def ensure_dirs(dry_run: bool = False):
    """Ensure category directories exist in OpenViking."""
    for cat, dirname in CATEGORY_DIRS.items():
        uri = f"{AGENT_MEMORIES_URI}/{dirname}"
        if dry_run:
            print(f"  [DRY] mkdir {uri}")
            continue
        resp = ov_request("POST", "/api/v1/fs/mkdir", {"uri": uri})
        status = resp.get("status", "?")
        # "ok" or ALREADY_EXISTS are both fine
        if status == "ok":
            print(f"  ✅ mkdir {uri}")
        elif "ALREADY_EXISTS" in str(resp.get("error", "")):
            pass  # Already exists, fine
        else:
            print(f"  ⚠️  mkdir {uri}: {resp.get('error', '?')[:60]}")


def write_to_l2(entry_id: str, category: str, title: str, content: str,
                force: bool = False, dry_run: bool = False) -> str:
    """Write a single memory entry to L2. Returns status string."""
    dirname = CATEGORY_DIRS.get(category, "patterns")
    uri = f"{AGENT_MEMORIES_URI}/{dirname}/{entry_id}.md"

    md_content = f"""---
id: {entry_id}
category: {category}
title: {title}
source: L0-memory-sync
created: {datetime.now().strftime('%Y-%m-%d')}
---

# {title}

{content}
"""

    if dry_run:
        return "DRY_RUN"

    mode = "replace" if force else "create"
    payload = {"content": md_content, "mode": mode, "uri": uri}

    resp = ov_request("POST", "/api/v1/content/write", payload)
    status = resp.get("status", "?")

    if status == "ok":
        sem = resp.get("result", {}).get("semantic_updated", "?")
        return f"OK sem={sem}"
    else:
        err = resp.get("error", {})
        code = err.get("code", "") if isinstance(err, dict) else str(err)[:40]
        if code == "ALREADY_EXISTS":
            return "SKIP_EXISTS"
        elif "busy" in str(err).lower():
            return "BUSY(will_index)"
        else:
            return f"ERR:{code}"


def main():
    parser = argparse.ArgumentParser(description="L0→L2 Memory Sync")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be written")
    parser.add_argument("--force", action="store_true", help="Overwrite existing L2 entries")
    args = parser.parse_args()

    print(f"=== L0→L2 Memory Sync {'(DRY RUN)' if args.dry_run else ''} ===")
    print(f"OpenViking: {OPENVIKING_BASE}")

    # 1. Ensure directories
    print("\n[1] Ensuring category directories...")
    ensure_dirs(dry_run=args.dry_run)

    # 2. List existing L2 files (for skip logic)
    existing = set()
    if not args.force and not args.dry_run:
        print("\n[2] Scanning existing L2 entries...")
        existing = list_l2_files()
        print(f"  Found {len(existing)} existing L2 files")

    # 3. Read entries from stdin (JSON array) or use demo entries
    print("\n[3] Writing entries to L2...")
    entries = []
    if not sys.stdin.isatty():
        try:
            entries = json.loads(sys.stdin.read())
        except json.JSONDecodeError:
            print("  ❌ Invalid JSON on stdin", file=sys.stderr)
            sys.exit(1)
    else:
        # Demo mode: sync from MEMORY.md if it exists
        memory_md = os.path.expanduser("~/.hermes/MEMORY.md")
        if os.path.exists(memory_md) and os.path.getsize(memory_md) > 0:
            print("  Reading from MEMORY.md...")
            with open(memory_md) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("[") and "]" in line:
                        # Extract tags and content
                        bracket_end = line.index("]")
                        tag_part = line[:bracket_end + 1]
                        content_part = line[bracket_end + 1:].strip()
                        if content_part:
                            entries.append({
                                "id": f"mem-{len(entries):03d}",
                                "category": "pattern",
                                "title": content_part[:40],
                                "content": content_part,
                            })

    if not entries:
        print("  No entries to sync. Pass JSON array via stdin or populate MEMORY.md.")
        return

    stats = {"ok": 0, "skip": 0, "err": 0, "dry": 0}
    for entry in entries:
        eid = entry.get("id", f"entry-{stats['ok']+stats['skip']+stats['err']}")
        cat = entry.get("category", "pattern")
        title = entry.get("title", eid)

        # Skip if already exists and not forced
        dirname = CATEGORY_DIRS.get(cat, "patterns")
        expected_uri = f"{AGENT_MEMORIES_URI}/{dirname}/{eid}.md"
        if not args.force and expected_uri in existing:
            stats["skip"] += 1
            print(f"  ⏭️  {eid} (exists)")
            continue

        result = write_to_l2(
            entry_id=eid,
            category=cat,
            title=title,
            content=entry.get("content", ""),
            force=args.force,
            dry_run=args.dry_run,
        )

        if result == "DRY_RUN":
            stats["dry"] += 1
            print(f"  [DRY] {eid} → {dirname}/{eid}.md")
        elif result.startswith("OK"):
            stats["ok"] += 1
            print(f"  ✅ {eid} → {dirname}/")
        elif result == "SKIP_EXISTS":
            stats["skip"] += 1
            print(f"  ⏭️  {eid} (exists)")
        elif result == "BUSY(will_index)":
            stats["ok"] += 1  # Written, just indexing
            print(f"  ✅ {eid} → {dirname}/ (indexing)")
        else:
            stats["err"] += 1
            print(f"  ❌ {eid} → {result}")

        time.sleep(0.3)  # Throttle to avoid "resource is busy"

    print(f"\n=== Done: {stats['ok']} written, {stats['skip']} skipped, {stats['err']} errors, {stats['dry']} dry ===")


if __name__ == "__main__":
    main()

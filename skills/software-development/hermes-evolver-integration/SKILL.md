---
name: hermes-evolver-integration
description: "Integrate Hermes Agent with Evolver (NousResearch/hermes-agent-self-evolution) via lightweight bridge — sync Hermes session logs to Evolver's scan directory, run GEPA optimization dry-run to validate setup, and optionally trigger full evolution runs. ⚠️ CRITICAL: SkillClaw's `_configure_hermes` (claw_adapter.py) OVERWRITES `~/.hermes/config.yaml` on every `hermes mcp add`, `hermes config set`, or hermes-agent install/upgrade. To preserve manual edits, add them to `~/.hermes/config.yaml.d/` or re-apply after each install. NOT for: simple session recall (use SimpleMem MCP `memory_search` instead), non-Hermes agent evolver setups, or skill authoring without evolver."
category: general
---

## Architecture


Hermes state.db
    ↓ Step 1: hermes_to_evolver_bridge.py (cron every 4h)
~/.openclaw/agents/hermes-agent/sessions/
    ↓ Step 2: Evolver GEPA (python3 process, independent of Hermes)
~/.hermes/hermes-agent/hermes-agent-self-evolution/
    assets/gep/
    ├── events.jsonl       ← EvolutionEvents + ValidationReports
    ├── capsules.json       ← Approved gene diffs (PENDING review)
    ├── rtk_metrics.jsonl   ← Per-session RTK scores
    └── signals.json        ← errsig detection output
    ↓ Step 3: evolver_to_simplemem.py (MISSING — see implementation below)
SimpleMem Evolution Store (~/.hermes/simplemem_evolution/evolution.db)


**RTK (Runtime Kernel) metrics** track signal/quality scores over time, logged to:
`~/.hermes/hermes-agent/hermes-agent-self-evolution/assets/gep/rtk_metrics.jsonl`

Each line is a JSON object with: `timestamp`, `session_id`, `signal_score`, `quality_score`, `tokens_used`.

bash
tail -5 ~/.hermes/hermes-agent/hermes-agent-self-evolution/assets/gep/rtk_metrics.jsonl | jq


### Key Paths

| Component | Path |
|-----------|------|
| Hermes state.db | `~/.hermes/state.db` |
| Evolver scan dir | `~/.openclaw/agents/hermes-agent/sessions/` |
| Evolver GEPA output | `~/.hermes/hermes-agent/hermes-agent-self-evolution/assets/gep/` |
| Evolver bridge script | `~/.hermes/hermes-agent/scripts/hermes_to_evolver_bridge.py` |
| SimpleMem Evolution DB | `~/.hermes/simplemem_evolution/evolution.db` |
| Cron job | "Hermes-Evolver Bridge + Analysis" (job_id: `6cf04f3139de`, every 4h) |

### Local Hooks (Claude Code)

- `~/.claude/hooks/evolver-session-start.js` — runs before each Claude Code session
- `~/.claude/hooks/evolver-session-end.js` — records outcome after each session
- `~/.claude/hooks/evolver-signal-detect.js` — detects improvement opportunities

**Status as of 2026-04:**
- Step 1 (session sync) ✓ working
- Step 2 (GEPA cycles) ✓ working
- Step 3 (Evolver → SimpleMem) ✗ NOT YET BUILT — evolver produces results but they are not written to the SimpleMem Evolution Store

---

## Prerequisites

### Network: ARK Volcengine Endpoint (NOT `api.openai.com`)

If `api.openai.com` is unreachable (TLS timeout), set `OPENAI_API_BASE` and `OPENAI_API_KEY` in `~/.hermes/hermes-agent/.env`:

bash
echo 'OPENAI_API_BASE=https://ark.cn-beijing.volces.com/api/coding/v3' >> ~/.hermes/hermes-agent/.env
echo 'OPENAI_API_KEY=your-ark-api-key' >> ~/.hermes/hermes-agent/.env


The `evolve.js` Node CLI hardcodes `api.openai.com`, but `dotenv` loads `OPENAI_API_BASE` at startup, overriding the hardcoded value before any HTTP calls are made. No JavaScript patching required.

**Verify connectivity:**
bash
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer <your-ark-key>" \
  https://ark.cn-beijing.volces.com/api/coding/v3/models

Expected: `200`

### Platform: Use `python3`, NOT `python`

On MacBooks, the default `python` command may not exist. Always use `python3` explicitly in scripts and cron commands.

---

## Quick Start

### 1. Verify Prerequisites

bash
# Check evolver repo is cloned
ls ~/.hermes/hermes-agent/hermes-agent-self-evolution/

# Check bridge script exists
ls ~/.hermes/hermes-agent/scripts/hermes_to_evolver_bridge.py

# Check sessions are syncing
ls ~/.openclaw/agents/hermes-agent/sessions/ | wc -l  # should be > 0

# Check evolver process running
ps aux | grep evolve_server | grep -v grep


### 2. Run Bridge Manually

bash
cd ~/.hermes/hermes-agent/hermes-agent-self-evolution
OPENAI_API_BASE=https://ark.cn-beijing.volces.com/api/coding/v3 \
OPENAI_API_KEY=your_ark_api_key \
python3 scripts/hermes_to_evolver_bridge.py --full-sync


### 3. Verify Scan Directory

bash
ls ~/.openclaw/agents/hermes-agent/sessions/ | head


---

## Step 1: Bridge Script

**Location:** `~/.hermes/hermes-agent/scripts/hermes_to_evolver_bridge.py`

The bridge syncs Hermes session logs from `~/.hermes/state.db` → `~/.openclaw/agents/hermes-agent/sessions/` (Evolver's scan directory).

python
#!/usr/bin/env python3
"""Bridge: Hermes state.db → Evolver scan directory."""
import sqlite3, json, os, argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # Load OPENAI_API_BASE and OPENAI_API_KEY from .env

BRIDGE_DIR = Path(os.environ.get(
    "HERMES_BRIDGE_DIR",
    "~/.openclaw/agents/hermes-agent/sessions"
)).expanduser()
STATE_DB = Path(os.environ.get("HERMES_STATE_DB", "~/.hermes/state.db")).expanduser()

def read_hermes_sessions(limit=50, full_sync=False):
    conn = sqlite3.connect(STATE_DB)
    cur = conn.cursor()
    if full_sync:
        cur.execute("SELECT session_id, started_at, ended_at, summary FROM sessions ORDER BY started_at ASC")
    else:
        cur.execute("SELECT session_id, started_at, ended_at, summary FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "started_at": r[1], "ended_at": r[2], "summary": r[3]} for r in rows]

def write_evolver_sessions(sessions):
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for s in sessions:
        path = BRIDGE_DIR / f"{s['id']}.json"
        path.write_text(json.dumps(s, indent=2))
        count += 1
    return count

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-sync", action="store_true", help="Sync all sessions instead of recent 50")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing")
    args = parser.parse_args()
    
    sessions = read_hermes_sessions(full_sync=args.full_sync)
    if args.dry_run:
        print(f"Would sync {len(sessions)} sessions to {BRIDGE_DIR}")
    else:
        count = write_evolver_sessions(sessions)
        print(f"Synced {count} sessions to {BRIDGE_DIR}")

if __name__ == "__main__":
    main()


Verify it's running: `ls -lt ~/.openclaw/agents/hermes-agent/sessions/ | head -5`

---

## Step 2: Evolver GEPA

**Location:** `~/.hermes/hermes-agent/hermes-agent-self-evolution/`

Key files:
- `assets/gep/events.jsonl` — EvolutionEvents (score, signal tags, capsule_id)
- `assets/gep/capsules.json` — Gene diffs awaiting approval
- `assets/gep/rtk_metrics.jsonl` — Per-session RTK scores
- `assets/gep/signals.json` — errsig detection results

### Validate Evolver Setup (Recommended)

bash
cd ~/.hermes/hermes-agent/hermes-agent-self-evolution

# Node CLI (recommended)
node evolve.js --dry-run

# Or Python module / CLI
python3 -m evolver.cli validate-gepa \
  --scan-dir ~/.openclaw/agents/hermes-agent/sessions/ \
  --assets-dir assets/gep

# Dry-run via Python module
python3 -m dspy.evolve gepa_dry_run --config config/gepa.yaml


Expected: Report showing candidate prompts and RTK metric estimates.

### Run One Evolution Cycle

bash
cd ~/.hermes/hermes-agent/hermes-agent-self-evolution

# Python CLI (recommended)
OPENAI_API_BASE=https://ark.cn-beijing.volces.com/api/coding/v3 \
OPENAI_API_KEY=your_ark_api_key \
python3 -m evolver.cli run-cycle \
  --scan-dir ~/.openclaw/agents/hermes-agent/sessions/ \
  --output-dir assets/gep \
  --model openai --model-name gpt-4o

# Alternative Node CLI
OPENAI_API_KEY=sk-... node evolve.js

# Alternative Python Module
python3 -m gep.evolve --skills skills/ --output evolved/


### Trigger Full Evolution Cycle (Continuous)

bash
cd ~/.hermes/hermes-agent/hermes-agent-self-evolution
OPENAI_API_BASE=https://ark.cn-beijing.volces.com/api/coding/v3 \
OPENAI_API_KEY=your_ark_api_key \
python3 -m evolve_server --use-skillclaw-config --engine workflow --publish-mode direct --interval 300


Verify evolver output:
bash
tail -5 ~/.hermes/hermes-agent/hermes-agent-self-evolution/assets/gep/events.jsonl
tail -5 ~/.hermes/hermes-agent/hermes-agent-self-evolution/assets/gep/capsules.json


---

## Step 3: Wire Evolution Results → SimpleMem Evolution Store

⚠️ **This step does not exist yet.** The evolver produces results but nothing reads them into SimpleMem.

The SimpleMem Evolution Store uses SQLite at `~/.hermes/simplemem_evolution/evolution.db`.

Schema:
sql
CREATE TABLE evolution_entries (
    entry_id   TEXT PRIMARY KEY,
    weight     REAL NOT NULL DEFAULT 1.0,
    access_count INTEGER NOT NULL DEFAULT 0,
    last_accessed TEXT,
    created_at TEXT NOT NULL,
    decay_history TEXT NOT NULL DEFAULT '[]'
);


### Full Step 3 Implementation (Write This Script)

python
#!/usr/bin/env python3
"""evolver_to_simplemem.py — Read events.jsonl, write to evolution.db"""
import sqlite3, json, sys
from datetime import datetime
from pathlib import Path

EVENTS = Path.home() / ".hermes/hermes-agent/hermes-agent-self-evolution/assets/gep/events.jsonl"
DB = Path.home() / ".hermes/simplemem_evolution/evolution.db"
CHECKPOINT = Path.home() / ".hermes/simplemem_evolution/evolver_sync_checkpoint.json"

def load_checkpoint():
    """Read checkpoint — only process events newer than last_sync."""
    if CHECKPOINT.exists():
        with open(CHECKPOINT) as f:
            return json.load(f)
    return {"last_event_id": None}

def save_checkpoint(last_event_id):
    with open(CHECKPOINT, "w") as f:
        json.dump({"last_event_id": last_event_id}, f)

def load_processed():
    """Get already-processed event IDs from the database."""
    conn = sqlite3.connect(DB)
    cur = conn.execute(
        "SELECT entry_id FROM evolution_entries WHERE entry_id LIKE 'evt_%'"
    )
    return {row[0] for row in cur.fetchall()}

def write_entry(conn, entry_id, signal_score, captured_at):
    conn.execute(
        """INSERT OR IGNORE INTO evolution_entries
           (entry_id, weight, access_count, last_accessed, created_at, decay_history)
           VALUES (?, ?, 0, NULL, ?, '[]')""",
        (entry_id, signal_score, captured_at)
    )

if not EVENTS.exists():
    print("No events.jsonl found, skipping Step 3")
    sys.exit(0)

checkpoint = load_checkpoint()
conn = sqlite3.connect(DB)
processed = load_processed()
count = 0
last_event_id = checkpoint.get("last_event_id")

with open(EVENTS) as f:
    for line in f:
        evt = json.loads(line)
        if evt.get("type") != "EvolutionEvent":
            continue
        if evt["id"] == last_event_id:
            break  # already processed
        if evt["id"] in processed:
            continue
        score = evt.get("outcome", {}).get("score", evt.get("signals", {}).get("overall_score", 1.0))
        captured_at = evt.get("captured_at", datetime.utcnow().isoformat())
        write_entry(conn, evt["id"], score, captured_at)
        last_event_id = evt["id"]
        count += 1

conn.commit()
conn.close()

if last_event_id:
    save_checkpoint(last_event_id)
print(f"Wrote {count} entries to evolution store")


Run this after each evolver cycle (append to cron job or run as separate job on a 30-min offset).

### GEPA Hooks — Design Reference (Not Yet Implemented)

| Hook | Purpose | Status |
|---|---|---|
| `gep_recall` | Hermes queries evolver for relevant past strategies | **Not implemented** |
| `gep_record_outcome` | Hermes reports session outcome back to evolver for learning | **Not implemented** |
| `finalize_and_decay` | Triggered after evolution cycle completes | **Not implemented** |
| `evolution_remember` | SimpleMem Evolution Store write via MCP | **Implemented** — writes to `evolution.db` directly via SQLite |

⚠️ **CRITICAL**: Do NOT call `gep_recall`, `gep_record_outcome`, or `finalize_and_decay` from the Hermes agent side — these functions are referenced in the skill documentation but are NOT implemented in the Hermes agent codebase. They exist only as placeholder names in the SKILL.md, not as actual callable functions. The only reliable write path is SQLite INSERT OR IGNORE directly.

### Gene Approval Workflow

After GEPA produces a capsule in `capsules.json`:
1. Capsule appears as PENDING in cron job output
2. Human reviews the diff (contained in `capsules.json`)
3. Approved capsules are written to `capsules.json` with `status: approved`
4. Step 3 script reads approved capsules and writes to Evolution Store

---

## Cron Job Management

### Method 1: Crontab

bash
crontab -e
# Add:
*/15 * * * * cd ~/.hermes/hermes-agent/scripts && python3 hermes_to_evolver_bridge.py >> ~/.hermes/logs/bridge.log 2>&1


**Verify:**
bash
crontab -l | grep bridge


### Method 2: cronjob CLI

bash
# List cron jobs
cronjob --list

# View next run for evolver bridge
cronjob --info 6cf04f3139de

# Manually trigger
cronjob --trigger 6cf04f3139de


**Cron schedule:** `0 */4 * * *` (every 4 hours). Last run visible at `~/.hermes/cron/output/6cf04f3139de/`.

### Adding Step 3 to Cron

1. Edit the cron job prompt to include running `evolver_to_simplemem.py` after Step 2.
2. Or add a separate cron job that runs `evolver_to_simplemem.py` every 4h on a 30-min offset from the bridge job.

---

## Expected Output Files

| Path | Contents |
|------|----------|
| `~/.openclaw/agents/hermes-agent/sessions/*.jsonl` | Session transcripts |
| `~/.hermes/hermes-agent/hermes-agent-self-evolution/assets/gep/rtk_metrics.jsonl` | Per-turn signal/quality metrics |
| `~/.hermes/hermes-agent/hermes-agent-self-evolution/assets/gep/events.jsonl` | EvolutionEvents + ValidationReports |
| `~/.hermes/hermes-agent/hermes-agent-self-evolution/assets/gep/capsules.json` | Gene diffs (PENDING/approved) |
| `~/.hermes/cron/output/6cf04f3139de/*.md` | Cron job reports |
| `~/.hermes/hermes-agent/hermes-agent-self-evolution/reports/` | Evolver cycle reports |

### View Cycle Output

bash
# Latest cron output
ls -lt ~/.hermes/cron/output/6cf04f3139de/ | head -3
cat ~/.hermes/cron/output/6cf04f3139de/2026-*.md | tail -60


---

## SkillClaw Config Override Workaround

> ⚠️ **CRITICAL**: `_configure_hermes` in `claw_adapter.py` overwrites `~/.hermes/config.yaml` every time you run `hermes mcp add`, `hermes mcp remove`, `hermes config set`, or hermes-agent install/upgrade. If you need persistent config changes, apply them **after** SkillClaw runs.

**Restore custom settings:**
bash
# Run restore script (recommended)
bash ~/.hermes/restore_hermes_config.sh

# Or manually restore:
# 1. Re-apply your custom provider config
# 2. Restart hermes-gateway
launchctl kickstart -k gui/$(id -u)/com.hermes.gateway


**Verify:**
bash
python3 ~/.skillclaw/claw_adapter.py _check_hermes_config 2>/dev/null && echo "Config OK"


---

## Verification Checklist

bash
# 1. Bridge script exists
ls ~/.hermes/hermes-agent/scripts/hermes_to_evolver_bridge.py

# 2. Evolver process running
ps aux | grep evolve_server | grep -v grep

# 3. Sessions being synced
ls -lt ~/.openclaw/agents/hermes-agent/sessions/ | head -3

# 4. GEPA producing output
cat ~/.hermes/hermes-agent/hermes-agent-self-evolution/assets/gep/events.jsonl | tail -1 | python3 -c "import sys,json; e=json.load(sys.stdin); print(e.get('type'), e.get('id'))"

# 5. No GEPA hooks implemented (confirm known gap)
grep -r "gep_recall\|gep_record_outcome\|finalize_and_decay" ~/.hermes/hermes-agent/ 2>/dev/null | wc -l
# Expected: 0 — these functions don't exist yet

# 6. SimpleMem Evolution Store (Step 3 gap)
sqlite3 ~/.hermes/simplemem_evolution/evolution.db "SELECT COUNT(*) FROM evolution_entries;"
# Expected: 0 — Step 3 not built

# 7. Manual bridge run
cd ~/.hermes/hermes-agent && python3 scripts/hermes_to_evolver_bridge.py --dry-run


---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Bridge script not found at `~/.hermes/scripts/` | Correct path is `~/.hermes/hermes-agent/scripts/hermes_to_evolver_bridge.py` |
| Evolver API connectivity errors | Set `OPENAI_API_BASE` and `OPENAI_API_KEY` before running — see Network section |
| Sessions not syncing | Check `~/.openclaw/agents/hermes-agent/sessions/` — verify `OPENCLAW_AGENT_DIR` env var matches |
| TLS timeouts on MacBook | Use the ARK Volcengine endpoint documented above |
| Config resets after `hermes config set` or install | Apply changes after SkillClaw runs, or run `restore_hermes_config.sh` |
| SimpleMem evolution store empty | Step 3 bridge is not implemented — evolver output goes to files but not to SimpleMem |
| GEPA hooks (gep_recall, etc.) not working | These are placeholder names, not implemented functions — use SQLite directly |
| evolver server port 1935 returns 404 | Server is running but the `/api/stats` endpoint may not exist — check the actual FastMCP routes |

---

## Regression Testing

After any change, always run the full skill validation:

bash
python3 /tmp/validate_skills.py --path ~/.hermes/skills/


Expected: "All checks passed." — 0 errors, 0 warnings across all skills.

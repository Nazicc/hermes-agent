---
name: pokemon-player
description: "Use when playing Pokemon games autonomously via headless emulation. Starts a game server, reads structured game state from RAM, makes strategic decisions, and sends button inputs — all from the terminal. NOT for: non-Pokemon games, other game emulation, competitive online battles, real-time gaming, or when visual feedback is required."
category: general
---

## Architecture

- **pyboy** — pure Python Game Boy emulator; run headless (`--disable-render`)
- **Lua scripts** — embedded in save state; read/write RAM, push button combos
- **game-server.py** — Flask API wrapping pyboy + Lua bridge; exposes RAM addresses as REST endpoints
- **strategy/** — decision engine (type advantages, move priority, HP thresholds)
- **button_inputs/** — pre-built combo sequences (grinding, shiny hunting, etc.)

## Use when

- Playing Pokemon games automatically
- Training Pokemon for battle strategies
- Completing in-game tasks and quests
- Mass catching or farming Pokemon
- Testing game logic and mechanics
- Running Pokemon game automation on servers

## Startup

bash
# 1. Start game server
cd ~/.hermes/pokemon-player
python game-server.py --rom PokemonRed.gb --port 5000 &

# 2. Verify server is up
curl http://localhost:5000/health  # should return {"status": "ok", "state": "playing"}

# 3. Check RAM is readable
curl http://localhost:5000/ram?addr=0xC000  # HP of first party Pokemon


## RAM Map (Pokemon Red/Blue)

| Address | Size | Description |
|---------|------|-------------|
| 0xC000–0xC04F | 80 | Party Pokemon (6 × 44 bytes each) |
| 0xD058 | 1 | Current HP (low byte) |
| 0xD059 | 1 | Current HP (high byte) |
| 0xD016 | 1 | Current menu/overworld state |
| 0xD05E | 1 | Battle state (0=none, 1=enemy appeared, 2=battle) |
| 0xCC4B | 1 | Badge flags |
| 0xD721 | 1 | Pokemon caught flag |

## Key Endpoints

- `GET /ram?addr=0xXXXX` — read raw RAM at hex address
- `GET /party` — parse all 6 Pokemon: species, level, HP, status
- `GET /battle` — current battle state, enemy Pokemon, available moves
- `POST /button` — send a button press: `{"button": "A"}`, `{"button": "START"}`, etc.
- `POST /combo` — send a sequence: `{"sequence": ["LEFT", "A", "DOWN", 0.1, ...]}` (timestamps in seconds)
- `POST /save?name=mysave.state` — persist emulator state
- `GET /health` — health check

## Usage

bash
# Basic gameplay
curl -X POST http://localhost:5000/button -d '{"button":"A"}'

# Grind XP for 5 minutes (battles, then run)
curl -X POST http://localhost:5000/combo -d '{"sequence":["A",0.5,"LEFT",0.3,"A",0.5,"B",0.1],"loop":120}'

# Check party status
curl http://localhost:5000/party | jq '.[] | {species, level, hp}'

# Save progress
curl -X POST http://localhost:5000/save -d '{"name":"route1"}'

# Load saved state
curl -X POST http://localhost:5000/load -d '{"name":"route1"}'


## Batch File Modification Lessons (from skill evolution sessions)

When performing batch modifications to skill files (SKILL.md, JSON configs, YAML frontmatter), the following patterns were validated across 6+ agent sessions:

### 1. Always Verify Immediately with read_file, Not search_files

The patch tool may report `{"success": true}` even when changes don't persist to disk. Always read the file back immediately after patching to confirm:

bash
# WRONG: Trust patch success response
patch ... && echo "done"  # patch says OK but file unchanged

# RIGHT: Immediately read back to verify
patch ...
read_file(path, limit=5)  # confirm new content is actually there


### 2. Multiline YAML Block Scalars Need Careful Handling

Descriptions using `>`, `>-`, or `|` YAML multiline syntax are collapsed to single-line strings when patched. This changes the character count and can cause truncation. Always read the full multiline block first, then patch using the exact original string:

yaml
# BEFORE (multiline block scalar)
description: >
  Description text that
  spans multiple lines.

# AFTER (single-line string)
description: "Description text that spans multiple lines."


### 3. Patch Tool May Report Success Without Persisting

Across sessions, the patch tool returned `success: true` with valid diffs but the filesystem was not updated. When this happens:
- Re-read the file to see the current state
- Apply the patch again with the exact current string (not the string from before the failed patch)
- If a third attempt fails, consider using `terminal` with `sed` or direct file write

### 4. Batch Sizing: 5 Files Per Round is Optimal

Sessions that attempted larger batches (10-20 files) had higher failure rates due to:
- Stale context between reads and patches
- Cumulative string-matching drift
- No mid-batch verification

Optimal pattern:


read_file batch (5 files)
 ↓
patch batch (5 files)
 ↓
verify batch (5 files)
 ↓
repeat


### 5. search_files Caching vs. read_file Freshness

`search_files` may return cached/stale results showing new content that `read_file` doesn't yet show. Always use `read_file` as the source of truth for verification. Use `search_files` only for initial discovery (e.g., "which files contain this pattern").

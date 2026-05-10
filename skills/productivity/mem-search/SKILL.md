---
name: mem-search
description: "Three-layer memory search protocol for SimpleMem/MemPalace. Step 1: semantic index search → Step 2: timeline context → Step 3: fetch full entries. Covers session_search (long-term), search_memories (vector), sirchmunk (local files), and AMP-typed memories. Saves tokens by filtering before fetching full details. Trigger: user asks to search memory, find past sessions, recall previous work, look up a decision, check what was tried before, or query the agent's long-term memory. NOT for: current conversation context, filesystem search, or real-time web search."
category: general
---

## Three-Layer Memory Search Protocol

Use this skill whenever a user asks to search memory, find past sessions, recall previous work, look up a decision, check what was tried before, or query the agent's long-term memory system.

> **Token-saving rule**: Never fetch full session details before Layer 1 narrows the scope. Session files can be 50KB+.

---

## Layer 1 — Semantic Index Search

Always start here. Query the vector/keyword index to find candidate entries.

### Primary: `search_memories`

python
search_memories(query="<search terms>", top_k=5)


Returns ranked entry IDs + relevance scores. Use for natural-language queries.

### Secondary: `session_search`

python
session_search(query="<search terms>", limit=10)


Search across all historical sessions by keyword/timeline. Returns session IDs + snippets.

**Query construction**:
- Be specific: include project names, dates, tool names, or error messages
- For decisions: `"decision about X architecture"` or `"chose Y over Z"`
- For work: `"implemented feature X"` or `"debugged Y issue"`
- For lessons: `"learned that X causes Y"` or `"found workaround for Z"`

**Examples**:
- `"python fastmcp server debugging timeout"` → debug sessions
- `"decided to use pgvector over qdrant"` → architecture decisions
- `"hermes-agent skill evolution mem-search"` → skill's own development

**If Layer 1 returns nothing**: Try broader terms, synonyms, or date range queries.

**Skip to Layer 2**: When Layer 1 returns candidate session IDs.

---

## Layer 2 — Timeline Context

If Layer 1 returns candidate session IDs, fetch timeline context to understand scope.

### Tool: `get_session`

python
get_session(session_id="<id from Layer 1>")


Returns session metadata: timestamp, duration, topic summary, key operations, outcome.

### Tool: `list_sessions`

python
list_sessions(limit=20, type_filter=None)


List recent sessions to find the right time window. Useful when Layer 1 fails.

**When to skip Layer 2**: If Layer 1 returns a single high-confidence match (score > 0.85), go directly to Layer 3.

---

## Layer 3 — Full Entry Fetch

Only after identifying the right session, fetch specific entries.

### Tool: `ask`

python
ask(query="<specific question>", entry_ids=["<id1>", "<id2>"], mode="auto")


Synthesizes answers from given entries. Best for specific factual recall.

### Tool: `search_typed_memories` (AMP protocol)

python
search_typed_memories(query="<question>", memory_type="<type>", limit=10)


For type-filtered retrieval of AMP-typed memories.

### Tool: `sirchmunk` (offline fallback)

bash
sirchmunk query="<search>" path="~/.simplemem/exports/" limit=20


Search local memory export files. Use when MCP server is down or for bulk analysis.

---

## AMP Typed Memory System

SimpleMem supports typed memory entries for structured recall.

### Entry Types

| Type | Use For |
|------|---------|
| `lesson` | Pattern or insight to remember |
| `decision` | Architectural or design choice with rationale |
| `context` | Background information for future sessions |
| `observation` | Noted behavior or fact |
| `error` | Known bug or failure mode |
| `reference` | Documentation or external resource |
| `checkpoint` | Milestone or state marker |
| `reflection` | Post-mortem or review note |
| `preference` | User/system preference |
| `fact` | Verified factual information |
| `procedure` | How-to or step sequence |

### Tools

**Store a typed memory:**
python
store_typed_memory(content="<text>", memory_type="<type>", tags=["<tag1>"], session_id=None)


**Search by type:**
python
search_typed_memories(query="<search>", memory_type="<type>", limit=10)


**Check system status:**
python
memory_status()

Returns memory counts by type and storage backend health.

**List available types:**
python
list_memory_types()


---

## Quick Reference

| Need | Tool | Layer |
|------|------|-------|
| Natural language search | `search_memories` | L1 |
| Keyword/timeline search | `session_search` | L1 |
| Session metadata | `get_session` | L2 |
| Recent sessions list | `list_sessions` | L2 |
| Specific factual recall | `ask` | L3 |
| Local export search | `sirchmunk` | L3 |
| Store typed memory | `store_typed_memory` | — |
| Search typed memories | `search_typed_memories` | — |
| Check memory health | `memory_status` | — |
| List memory types | `list_memory_types` | — |
| Current session | — | Already in context window |

---

## Common Patterns

### Pattern 1: Recalling a Past Decision
1. Layer 1: `session_search("chose X over Y")`
2. Layer 2: `get_session(session_id)` to confirm scope
3. Layer 3: `ask("What was the rationale for choosing X?")`

### Pattern 2: Finding a Past Workaround
1. Layer 1: `session_search("error X workaround")`
2. Layer 2: Confirm session scope
3. Layer 3: `search_typed_memories("workaround for error X", type="error")`

### Pattern 3: Checking What Was Already Tried
1. Layer 1: `session_search("tried X approach for project Y")`
2. Layer 2: Timeline to see chronological attempts
3. Layer 3: Fetch specific entries about X approach

### Pattern 4: Remembering a Lesson
1. Layer 1: `search_typed_memories("python fastmcp", type="lesson")`
2. Layer 3: Directly retrieve typed memories by type filter

---

## Error Handling

| Error | Fallback |
|-------|----------|
| MCP client closed / `search_memories` connection error | Use `sirchmunk` on local exports at `~/.simplemem/exports/` |
| No results from `search_memories` | Try `session_search` with broader terms, then `list_sessions` |
| `ask` returns no answer | Verify entry IDs (Layer 2), then try direct `read_file` on export files |
| `memory_status` shows unhealthy | Check SimpleMem service is running; use `sirchmunk` as offline fallback |
| Session ID not found | Session may have been garbage-collected; retry Layer 1 with different terms |
| Too many results | Increase `top_k` or add more specific search terms |

---

## Quality Redlines

- Verify MCP tools are loaded before use (simplemem MCP must be connected)
- `session_search` works on closed sessions; for active session use direct context
- Always search index first (Layer 1), only fetch full on relevance (Layer 3)
- Do not use `search_memories` as a replacement for `read_file` — memory is for past conversations, not current files
- Do not call `ask` before Layer 1 narrows scope — you need entry IDs first
- Do not skip Layer 2 when you have session IDs — timeline context prevents hallucinating details from the wrong session
- Do not over-fetch — start with `top_k=5`, increase only if needed
- Do not store everything as `observation` — use the AMP taxonomy to enable type-filtered retrieval

---

## Anti-Triggers

- **Current conversation context** → Already in context window; use direct context
- **File content search** → Use `read_file` or terminal with `find`/`grep`
- **Filesystem search** → Use terminal with `find`/`grep`
- **Real-time web search** → Use duckduckgo-search or similar
- **Fresh context needed** → Rely on current session, not memory

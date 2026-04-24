# Skills Quality MCP Integration — BDD Specification

## Context

The `skills_quality` module exposes quality checks as an MCP server (FastMCP) so hermes-agent can:
1. Validate individual skills on-demand
2. Run full quality reports without leaving the chat
3. Get improvement suggestions for specific skills
4. Detect broken references before they cause issues

This document specifies the MCP tool interface and integration details.

---

## Feature 1: MCP Server Lifecycle

### Scenario: MCP server initializes with correct paths

**Given** the MCP server starts
**When** initialization runs
**Then** it sets `skills_dir` to `~/.hermes/skills/`
**And** it sets `hermes_agent_dir` to the hermes-agent installation path
**And** it does NOT pre-scan all skills (lazy loading)

### Scenario: MCP server handles missing skills directory

**Given** the skills directory does not exist
**When** any tool is called
**Then** it returns error `SKILLS_DIR_NOT_FOUND`
**And** the error message includes the expected path

---

## Feature 2: `quality_validate_skill` Tool

### Tool Signature

```
quality_validate_skill(skill_name: str) -> str
```

### Scenario: Validate a well-formed skill

**Given** skill `spec-driven-development` exists and is well-formed
**When** `quality_validate_skill` is called with `skill_name="spec-driven-development"`
**Then** it returns a human-readable string:

```
✅ spec-driven-development (workflow, 320 lines, full profile)

Structural Checks:
  ✅ Has ## Purpose section
  ✅ Has ## Key Concepts section
  ✅ Has ## Examples section
  ✅ Has ## Anti-Patterns section (3 named failure modes)
  ✅ Has cross-references (5 skills referenced)

Pedagogic Score: 8/10 — Good
  Teaching: 2/2
  Anti-Patterns: 2/2 (Feature Factory, Gold Plating, Scope Creep)
  Examples: 2/2 (3 examples including edge cases)
  When NOT to Use: 1/2 (mentions boundary)
  Cross-References: 1/2 (5 references, could deepen)

Errors: none
Warnings: NO_TRIGGERS (has score 8, triggers recommended)
```

### Scenario: Validate a stub skill

**Given** skill `systematic-debugging` exists but is a stub
**When** `quality_validate_skill` is called with `skill_name="systematic-debugging"`
**Then** it returns:

```
⚠️ systematic-debugging (unknown, 12 lines, stub profile)

Structural Checks:
  ✅ Has name in frontmatter
  ✅ Has description in frontmatter
  ❌ MISSING: No markdown sections (only frontmatter)
  ❌ MISSING: No ## Purpose section
  ❌ MISSING: No ## Application section

Pedagogic Score: 2/10 — Stub
  Teaching: 0/2 (absent)
  Anti-Patterns: 0/2 (absent)
  Examples: 0/2 (absent)
  When NOT to Use: 0/2 (absent)
  Cross-References: 0/2 (absent)

Errors: NO_SECTIONS, MISSING_REQUIRED_SECTION
Warnings: STUB_SKILL (needs major work)
```

### Scenario: Validate nonexistent skill

**Given** skill `nonexistent-skill` does not exist
**When** `quality_validate_skill` is called
**Then** it returns:
```
❌ Skill 'nonexistent-skill' not found.

Similar skills: systematic-debugging (Levenshtein distance: 3)
Did you mean one of: test-driven-development, spec-driven-development, incremental-implementation?
```

---

## Feature 3: `quality_score_skill` Tool

### Tool Signature

```
quality_score_skill(skill_name: str) -> str
```

### Scenario: Score a skill's pedagogic depth

**Given** skill `spec-driven-development`
**When** `quality_score_skill` is called
**Then** it returns a formatted score card:
```
📊 Pedagogic Depth Score: spec-driven-development

Teaching (Why This Works):  2/2 ⭐⭐
Anti-Patterns:              2/2 ⭐⭐  (Feature Factory, Gold Plating, Scope Creep)
Examples:                   2/2 ⭐⭐  (3 examples: good/bad/edge)
When NOT to Use:            1/2 ⭐    (mentions 1 boundary condition)
Cross-References:           1/2 ⭐    (5 refs, could form deeper graph)

───────────────────────────────────────
TOTAL: 8/10 — Good

Compared to PM-Skills standard (7/10 minimum): ✅ PASS
Top gap: "When NOT to Use" — add explicit boundary conditions
```

---

## Feature 4: `quality_check_references` Tool

### Tool Signature

```
quality_check_references(skill_name: str) -> str
```

### Scenario: Check references for a workflow skill

**Given** skill `discovery-process` (workflow) references `problem-statement`, `customer-journey-mapping-workshop`, etc.
**When** `quality_check_references` is called
**Then** it returns:
```
🔗 Reference Check: discovery-process

Referenced skills:
  ✅ skills/problem-statement/SKILL.md — EXISTS
  ✅ skills/customer-journey-mapping-workshop/SKILL.md — EXISTS
  ✅ skills/opportunity-solution-tree/SKILL.md — EXISTS
  ❌ BROKEN: skills/nonexistent/SKILL.md

Referenced by:
  ✅ skills/product-strategy-session/SKILL.md
  ✅ skills/leadership-transition/SKILL.md

Graph position: Interior node (3 incoming, 2 outgoing)
```

### Scenario: No broken references

**Given** skill has all valid references
**When** `quality_check_references` is called
**Then** it returns all green checks and notes the graph position

---

## Feature 5: `quality_report_all` Tool

### Tool Signature

```
quality_report_all(limit: int = 10, tier: str = "all", sort: str = "score") -> str
```

Parameters:
- `limit`: Max skills to return (default 10)
- `tier`: Filter by `stub|developing|good|excellent|all` (default `all`)
- `sort`: Sort by `score|lines|name|improvement` (default `score`)

### Scenario: Generate summary quality report

**Given** no filter parameters
**When** `quality_report_all` is called
**Then** it returns a compact summary:

```
📋 Hermes Skills Quality Report

Total: 111 skills

🗼 Stubs (0-3/10):        23 skills  ████████░░ 20.7%
📈 Developing (4-6/10):    45 skills  ████████████████████ 40.5%
✅ Good (7-8/10):          30 skills  ████████████░░░░░░░ 27.0%
⭐ Excellent (9-10/10):    13 skills  █████░░░░░░░░░░░░░░ 11.7%

Top 10 by Pedagogic Score:
  1. ⭐⭐ spec-driven-development      8/10
  2. ⭐⭐ test-driven-development     8/10
  3. ⭐⭐ systematic-debugging         7/10
  ...

⚠️ 7 broken references detected
🔄 1 circular reference: A→B→A
```

### Scenario: Filter by stub tier

**Given** `tier="stub"`
**When** `quality_report_all` is called
**Then** only stub skills (score ≤ 3) are listed

---

## Feature 6: `quality_find_stubs` Tool

### Tool Signature

```
quality_find_stubs() -> str
```

### Scenario: List all stub skills

**Given** 23 stub skills exist
**When** `quality_find_stubs` is called
**Then** it returns:
```
🚨 Stub Skills (23 found — need major work):

1. systematic-debugging (12 lines, 2/10)
2. planning-with-files (8 lines, 1/10)
3. dogfood (9 lines, 1/10)
...

These skills have only frontmatter — no Purpose, no Application, no Examples.
Run `quality_suggest_improvements` on any skill above for specific upgrade path.
```

---

## Feature 7: `quality_suggest_improvements` Tool

### Tool Signature

```
quality_suggest_improvements(skill_name: str) -> str
```

### Scenario: Get improvement suggestions for a stub

**Given** skill `systematic-debugging` is a stub
**When** `quality_suggest_improvements` is called
**Then** it returns:
```
💡 Improvement Path: systematic-debugging

Current State: Stub (2/10)
Target: Good (7/10 minimum)

Gap Analysis:
  ❌ Teaching (0→2): Add "Why This Works" — explain why systematic debugging works
  ❌ Anti-Patterns (0→2): Add "Anti-Patterns" — name 3 failure modes (e.g., "Symptom Surfing", "Fix-and-Sprint", "Blame Assignment")
  ❌ Examples (0→2): Add 2-3 examples — before/after, good/bad/debugging session trace
  ❌ When NOT to Use (0→1): Add boundary — "not for trivial bugs (< 5 min fix)"
  ⚠️ Cross-References (0→2): Add references to test-driven-development, subagent-driven-development

Priority Order:
  1. Add ## Purpose section (quickest win)
  2. Add ## Common Pitfalls with 3 named failure modes
  3. Add 2 examples with real debugging session traces
  4. Add ## When NOT to Use boundary

Estimated: 150-200 lines to reach Good (7/10)
```

---

## Feature 8: `quality_check_trigger` Tool

### Tool Signature

```
quality_check_trigger(skill_name: str) -> str
```

### Scenario: Check triggers for a skill

**Given** skill `context-engineering` has triggers defined
**When** `quality_check_trigger` is called
**Then** it returns:
```
🎯 Trigger Check: context-engineering

Trigger Coverage: 3/4
  ✅ Has ≥ 3 triggers (found: 9)
  ✅ Has Chinese triggers (found: 4)
  ⚠️ NO anti-triggers defined
  ✅ Has intent field

Trigger Keywords:
  - "context" (primary)
  - "setup context" (secondary)
  - "new session" (secondary)
  - "上下文" (Chinese)
  ...

Anti-Trigger Keywords: (none defined)

⚠️ Warning: Consider adding anti-triggers to prevent misfires
  Suggested: "already have context", "no session needed"
```

---

## Technical Requirements

### Dependencies
- `PyYAML` — already in hermes-agent venv
- `fastmcp` — MCP server framework

### Error Codes
| Code | Meaning |
|------|---------|
| `SKILL_NOT_FOUND` | Skill does not exist |
| `SKILLS_DIR_NOT_FOUND` | ~/.hermes/skills/ does not exist |
| `PARSE_ERROR` | YAML frontmatter or markdown parse failed |
| `BROKEN_REFERENCE` | Referenced skill file does not exist |
| `CIRCULAR_REFERENCE` | Skill A→B→A cycle detected |
| `STUB_SKILL` | Pedagogic score ≤ 3 |

### MCP Registration
```bash
hermes mcp add skills-quality \
  --command /Users/can/.hermes/hermes-agent/venv/bin/python \
  --args /Users/can/.hermes/hermes-agent/skills_quality/skills_quality_mcp.py
```

### Auto-start
The MCP server should be added to `~/.hermes/config.yaml` under `mcp_servers` so it starts with hermes-agent.

# Hermes Skills Quality Framework — BDD Specification

## Context

Hermes Skills (`~/.hermes/skills/`) contain 111 skills with wildly varying quality:
- **8–20 lines**: Stubs with only YAML frontmatter, no markdown content
- **100–700 lines**: Full skills with Purpose, Application, Examples, References

**Reference model**: Product-Manager-Skills (deanpeters) — 47 skills, all with:
- `intent` + `description` dual-layer fields
- Anti-Patterns sections naming failure modes
- "Why This Works" explanations
- "When to Use / When NOT to Use" clarity
- Cross-references forming a skill dependency graph

**Goal**: Build a quality framework that:
1. Validates skills against a quality standard
2. Scores pedagogic depth (teaching vs. just指令)
3. Detects cross-reference breakage
4. Generates actionable quality reports
5. Exposes checks as an MCP server for hermes-agent integration

---

## Feature 1: Skill Structure Validation

### Scenario: Valid skill passes all structure checks

**Given** a SKILL.md with all required sections
**When** the validator runs structure checks
**Then** it returns zero structural errors

**Required sections** (one of two profiles):

**Minimal Profile** (acceptable for skills < 50 lines):
- `name` in frontmatter
- `description` in frontmatter (≤ 200 chars, trigger-oriented "Use when...")

**Full Profile** (required for skills ≥ 50 lines):
- `name` in frontmatter
- `description` in frontmatter (≤ 200 chars)
- `intent` in frontmatter (richer explanation of purpose)
- `## Purpose` section (≥ 1 paragraph)
- `## Key Concepts` OR `## Application` section
- `## Examples` OR `## Common Pitfalls` section

### Scenario: Skill missing frontmatter name

**Given** a SKILL.md missing `name` in frontmatter
**When** the validator parses the frontmatter
**Then** it returns error `MISSING_NAME`
**And** the skill is flagged as non-invocable

### Scenario: Skill description exceeds 200 characters

**Given** a SKILL.md with `description` longer than 200 characters
**When** the validator checks description length
**Then** it returns error `DESCRIPTION_TOO_LONG`
**And** reports the actual length vs. limit

### Scenario: Skill missing required markdown sections (full profile)

**Given** a SKILL.md ≥ 50 lines missing `## Purpose`
**When** the validator checks section presence
**Then** it returns error `MISSING_REQUIRED_SECTION`
**And** lists which section is missing

### Scenario: Skill has content but zero markdown sections

**Given** a SKILL.md with content but no H2 headings (`##`)
**When** the validator checks for section headings
**Then** it returns error `NO_SECTIONS`
**And** suggests adding at least `## Purpose` and `## Application`

---

## Feature 2: Skill Type Classification

### Scenario: Classify skill type by structure

**Given** a SKILL.md
**When** the classifier runs
**Then** it categorizes as one of:

- **component**: Contains template/artifact sections, lacks multi-step phases
- **interactive**: Contains question patterns ("Ask...", "Follow-up...") or multi-turn flow markers
- **workflow**: Contains phase markers (Phase 1/2/3, Step 1/2/3), orchestrates other skills
- **unknown**: Cannot determine type from structure

### Scenario: Workflow skill references other skills

**Given** a workflow skill with `## Application` containing skill references
**When** the reference extractor runs
**And** referenced skills are missing from the filesystem
**Then** it returns error `BROKEN_SKILL_REFERENCE`
**And** lists the missing referenced skill names

### Scenario: Interactive skill missing enumerated options

**Given** a SKILL.md classified as interactive
**When** the validator checks for numbered options (1. / 2. / 3.)
**Then** if no options found, it returns warning `INTERACTIVE_NO_OPTIONS`
**And** suggests adding numbered next-step recommendations

---

## Feature 3: Pedagogic Depth Scoring

Inspired by PM-Skills "ABC: Always Be Coaching" principle.

### Scenario: Score pedagogic depth across 5 dimensions

**Given** a SKILL.md
**When** the pedagogic scorer runs
**Then** it scores each dimension 0–2:

| Dimension | 0 (absent) | 1 (minimal) | 2 (strong) |
|-----------|------------|-------------|------------|
| **Teaching** (`Why This Works` section) | No explanation section | One-line mention | Dedicated section with reasoning |
| **Anti-Patterns** (named failure modes) | No anti-patterns | Generic warning | Named failure modes with consequences |
| **Examples** | No examples | Single toy example | Multiple examples (good/bad/edge) |
| **When NOT to Use** | Absent | Vague | Explicit boundary conditions |
| **Cross-References** | No references | Single reference | Multiple references forming graph |

**Total score**: 0–10
- 0–3: **Stub** (needs major work)
- 4–6: **Developing** (has basics, needs depth)
- 7–8: **Good** (meets PM-Skills standard)
- 9–10: **Excellent** (pedagogic excellence)

### Scenario: Stub skill (score 0–3) is flagged

**Given** a SKILL.md with total pedagogic score ≤ 3
**When** the scorer completes
**Then** the skill is flagged as `STUB`
**And** listed in the quality report under "Needs Development"

### Scenario: Score components are individually reported

**Given** a SKILL.md with pedagogic score details
**When** the scorer returns results
**Then** each dimension is individually reported:
```
Teaching: 1/2 (minimal — has ## Why This Works but no reasoning)
Anti-Patterns: 0/2 (absent — no ## Anti-Patterns section)
Examples: 2/2 (strong — 3 concrete examples including edge cases)
When NOT to Use: 1/2 (minimal — mentions "not for X" but no boundary)
Cross-References: 1/2 (minimal — 1 reference, could form graph)
Total: 5/10 — Developing
```

---

## Feature 4: Cross-Reference Validation

### Scenario: Extract valid skill references

**Given** a SKILL.md containing `skills/SKILL.md` or `skills/skill-name/SKILL.md` patterns
**When** the reference extractor runs
**Then** it returns a list of referenced skill names

### Scenario: Broken skill references are detected

**Given** a SKILL.md references `skills/nonexistent-skill/SKILL.md`
**When** the reference validator checks the filesystem
**Then** it returns error `BROKEN_REFERENCE`
**And** the broken reference is listed with the skill that contains it

### Scenario: Build skill dependency graph

**Given** all SKILL.md files in the skills directory
**When** the graph builder runs
**Then** it returns a dict:
```
{
  "skills": {
    "spec-driven-development": {
      "references": ["test-driven-development", "systematic-debugging"],
      "referenced_by": ["incremental-implementation"]
    },
    ...
  },
  "orphans": ["dogfood", "obsidian", ...],  # skills that reference nothing and are not referenced
  "leaf_nodes": [...]  # skills with no incoming edges
}
```

### Scenario: Circular references are detected

**Given** skill A references B, and skill B references A
**When** the graph builder detects cycles
**Then** it returns warning `CIRCULAR_REFERENCE`
**And** lists the cycle path

---

## Feature 5: Trigger/TAnti-Trigger Validation

### Scenario: Skills without triggers are flagged

**Given** a SKILL.md missing `trigger` in frontmatter
**When** the trigger validator runs
**Then** if score ≥ 5, it returns warning `NO_TRIGGERS`
**And** suggests adding trigger keywords

### Scenario: Trigger and anti-trigger overlap

**Given** a SKILL.md with trigger `["debug", "fix"]` and anti-trigger `["don't debug", "don't fix"]`
**When** the trigger validator checks for overlap
**Then** if any anti-trigger is a negation of a trigger, it returns warning `TRIGGER_ANTITRIGGER_OVERLAP`

### Scenario: Trigger coverage score

**Given** a SKILL.md with triggers
**When** the scorer calculates trigger coverage
**Then** it returns a score based on:
- Has ≥ 3 triggers: +1
- Has Chinese triggers: +1
- Has anti-triggers: +1
- Has `intent` field: +1

---

## Feature 6: Quality Report Generation

### Scenario: Generate full quality report for all skills

**Given** the skills directory path
**When** the report generator runs
**Then** it returns a report with:

```
{
  "summary": {
    "total_skills": 111,
    "stubs": 23,
    "developing": 45,
    "good": 30,
    "excellent": 13,
    "broken_references": [...],
    "circular_references": [...]
  },
  "skills": [
    {
      "name": "spec-driven-development",
      "path": "skills/spec-driven-development/SKILL.md",
      "line_count": 320,
      "profile": "full",
      "type": "workflow",
      "pedagogic_score": 8,
      "pedagogic_breakdown": {...},
      "errors": [],
      "warnings": ["NO_ANTI_PATTERNS"],
      "references": ["test-driven-development", ...],
      "referenced_by": ["incremental-implementation"]
    },
    ...
  ],
  "top_improvements": [
    {
      "skill": "systematic-debugging",
      "current_score": 3,
      "potential_score": 8,
      "gap": "Missing ## Examples, ## Anti-Patterns, and ## Why This Works"
    }
  ]
}
```

### Scenario: Report filters by quality tier

**Given** a quality report
**When** filtering by `tier=stub`
**Then** only skills with pedagogic_score ≤ 3 are returned

### Scenario: Report sorts by improvement potential

**Given** a quality report
**When** sorting by `sort=improvement_potential`
**Then** skills are ordered by (potential_score - current_score) descending

---

## Feature 7: MCP Server Integration

### Scenario: Skills quality MCP server starts

**Given** the skills_quality_mcp.py is registered in hermes-agent
**When** hermes-agent starts
**Then** the MCP server is available with 7 tools:
1. `quality_validate_skill` — Validate single skill structure
2. `quality_score_skill` — Score pedagogic depth
3. `quality_check_references` — Validate cross-references
4. `quality_report_all` — Generate full quality report
5. `quality_find_stubs` — List all stub skills
6. `quality_suggest_improvements` — Get improvement suggestions
7. `quality_check_trigger` — Validate triggers/anti-triggers

### Scenario: MCP tool handles missing skill gracefully

**Given** a request for `quality_validate_skill` with a nonexistent skill name
**When** the tool handler runs
**Then** it returns error `SKILL_NOT_FOUND`
**And** suggests similar skill names (fuzzy match)

### Scenario: MCP server returns human-readable output

**Given** a request for `quality_report_all`
**When** the tool runs
**Then** the response is a formatted string suitable for display in chat
**And** includes emoji indicators for quality tiers

---

## Technical Constraints

- **Python version**: 3.11+ (hermes-agent venv)
- **Dependencies**: `PyYAML` (already in venv), `fastmcp` (for MCP server)
- **No network calls** in core validation logic (deterministic, offline-capable)
- **No file writes** in validation/scoring (read-only analysis)
- **Lazy loading**: Parse SKILL.md on-demand, not all at startup
- **Error isolation**: One skill's parse error doesn't crash the full report

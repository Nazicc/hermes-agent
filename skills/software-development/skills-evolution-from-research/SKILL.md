---
name: skills-evolution-from-research
description: Evaluate and integrate external open-source projects into Hermes Agent skills. Use when analyzing GitHub repos for potential skill improvements, or when upgrading skill standards based on external research.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skills, research, integration, github, open-source]
    related_skills: [cybersecurity-industry-research, github-repo-management]
---

# Skills Evolution from External Research

Evaluate an external open-source project and integrate high-value patterns into Hermes Agent skills.

## When to Use

- Analyzing a GitHub project for potential integration into skills
- Upgrading skill standards based on external research
- Merging insights from multiple similar projects
- When the user says "analyze X project" and you see integration potential

## Evaluation Framework

For any external project, assess across 4 dimensions:

| Dimension | What to Measure | Threshold for Integration |
|-----------|-----------------|---------------------------|
| **Scale** | Stars, forks, commits, contributors | >1000 stars or >500 commits = substantial |
| **Relevance** | How closely matches Hermes skills domain | Direct (same domain) vs indirect (analogous) |
| **Actionability** | Can patterns be directly implemented? | High (copy-paste code/templates) vs Low (theory only) |
| **Complementary** | Does it fill gaps in existing skills? | Gap-filling > redundant |

### Prioritization Matrix

```
                    High Actionability        Low Actionability
                 ┌─────────────────────────┬─────────────────────────┐
High Relevance   │  P0: Integrate now      │  P1: Extract concepts   │
                 │  (direct implementation) │  (theoretical only)     │
                 ├─────────────────────────┼─────────────────────────┤
Low Relevance    │  P2: File for later     │  P3: Skip               │
                 │  (if scale is huge)      │  (no action needed)     │
                 └─────────────────────────┴─────────────────────────┘
```

## Integration Process

### 1. Clone and Survey

```bash
# Clone with shallow history (faster)
git clone --depth 1 https://github.com/owner/repo.git /tmp/repo_name

# Count metrics
ls /tmp/repo_name                    # directory structure
find /tmp/repo_name -name "*.md" | wc -l  # markdown files
find /tmp/repo_name -name "*.py" | wc -l    # code files
wc -l /tmp/repo_name/README.md       # readme size
```

### 2. Identify High-Value Patterns

Look for these pattern types (ordered by actionability):

| Pattern Type | Indicator | Integration Effort |
|--------------|-----------|-------------------|
| **Templates** | `.yaml`, `.json`, `.md` files with structure | Low — copy-paste |
| **Agent Commands** | `.claude/commands/*.md` or similar | Low — standardize format |
| **Protocol Formats** | JSON Schema, structured handoff formats | Medium — adapt to Hermes format |
| **Workflow Definitions** | YAML phases, step definitions | Medium — generalize to skill format |
| **Gotchas/Warnings** | Lists of common mistakes, pitfalls | Low — add to existing skills |
| **Research Summaries** | Literature reviews, paper references | High effort — add as citations |

### 3. Map to Existing Skills

Find the most relevant existing skill(s) for each pattern:

```bash
# Find skills by keyword
search_files(pattern="keyword", path="$HERMES_SKILLS", target="files")
```

Principles:
- **Gotchas** → add to existing skill's Gotchas section
- **Templates/Protocols** → add as new section in relevant skill
- **Workflows** → add as `[workflow]` section (see format below)
- **Research** → add citations to relevant skills' Overview

### 4. Three-Way Merge for Multiple Projects

When analyzing similar projects (e.g., both `muratcankoylan/Agent-Skills` and `davidkimai/Context-Engineering`):

1. **Identify unique contributions per project**
2. **Find overlapping patterns** (both have Gotchas → consolidate format)
3. **Merge at the skill level** — don't duplicate, unify around best format
4. **Reference both sources** in the commit message

## Skill Section Templates

### [workflow] Section Format

Standardized workflow section for skills with multi-phase processes:

```markdown
## [workflow] <Skill Name> Protocol

Standardized workflow. Follow phases in order.

### Phase Flow

```
[phase1] → [phase2] → [phase3] → [verify] → [audit]
```

### Phase Definitions

```yaml
phases:
  - phase1:
      description: |
        What happens in this phase.
        - Sub-step A
        - Sub-step B
      output: What this phase produces
      gate: "When to stop and not proceed"

  - phase2:
      description: |
        Next phase description.
      output: Next output
```

### Protocol for delegate_task Handoffs

```yaml
handoff:
  protocol_version: "1.0.0"
  intent: "<clear statement of subagent goal>"

  input:
    task: "<specific task>"
    context: "<background>"
    constraints: ["<constraint 1>", "<constraint 2>"]

  process:
    - /phase1{action="description"}
    - /phase2{action="description"}

  output:
    result: "<what subagent produces>"
    quality: "<verification notes>"

  meta:
    version: "1.0.0"
    timestamp: "<ISO 8601>"
    fix_authorized: <true|false>
```
```

### Gotchas Integration

When adding gotchas from external research, use the shared `.gotchas/` knowledge base:

```bash
# Create new gotcha entry
# File: .gotchas/<id>.yaml
id: <unique-id>
title: <short title>
description: |
  Multi-line description of the gotcha.
severity: <high|medium|low|info>
tags: [<tag1>, <tag2>]
related_gotchas: [<other-gotcha-id>]
```

Then reference in skill:
```markdown
## Gotchas

- [<id>](#) — <one-line summary>
```

## Integration Checklist

Before committing:

- [ ] Project scale verified (stars/commits measured)
- [ ] All high-actionability patterns identified
- [ ] Patterns mapped to existing skills (no duplication)
- [ ] New gotchas added to `.gotchas/` if applicable
- [ ] `[workflow]` sections follow standard format
- [ ] Protocol Shell handoffs follow format above
- [ ] Commit message references source project(s)
- [ ] Changes tested (skills load correctly)

## Commit Message Format

```bash
git add -A && git commit -m "feat(skills): integrate <project-name> patterns

- <skill>: <what was added>
- <skill>: <what was added>
- ...

Inspired by <project-name> (<stars> stars) — <key insight>"
```

## Examples

### Example 1: davidkimai/Context-Engineering (8.8k stars)

**Scale:** 8.8k stars, 1,140 commits, MIT
**Relevance:** High — directly about context engineering for AI agents
**Actionability:** High — AgenticOS commands, Protocol Shell format, Cognitive Tools templates

**Integration:**
- Protocol Shell → `context-engineering` [workflow] section + `hermes-agent` handoff protocol
- Cognitive Tools → `context-engineering` Cognitive Tools section
- Both → commit references project + IBM Zurich 2025 research citation

### Example 2: muratcankoylan/Agent-Skills (15.2k stars)

**Scale:** 15.2k stars, MIT
**Relevance:** High — agent skill writing standards
**Actionability:** High — Gotchas format directly implementable

**Integration:**
- Gotchas mandatory section → skill template update
- Gotchas format → shared `.gotchas/` knowledge base
- Top skills → Gotchas added

## Critical Architecture: Dual Skills Directories

**Always verify which skills directory is active before editing.**

```
~/.hermes/skills/                           ← Hermes Agent RUNTIME reads from here
~/.hermes/hermes-agent/skills/              ← git-tracked SOURCE COPY (often stale)
```

**How to check:**
```bash
# Runtime skills directory (the one Hermes actually uses)
wc -l ~/.hermes/skills/<category>/<skill>/SKILL.md

# Git-tracked copy (may be outdated or diverge)
wc -l ~/.hermes/hermes-agent/skills/<category>/<skill>/SKILL.md
```

**Why this matters:**
- `~/.hermes/hermes-agent/skills/` is the git-tracked source tree — `git add`/`commit` work here
- `~/.hermes/skills/` is the runtime skills directory — Hermes Agent reads this at runtime
- They can have DIFFERENT content (different file sizes, different line counts)
- **Editing only the git-tracked copy does NOT update the runtime skills**

**Verification after editing a skill:**
```bash
# Check both paths have identical content
sha1sum ~/.hermes/skills/<path>/SKILL.md
sha1sum ~/.hermes/hermes-agent/skills/<path>/SKILL.md

# If different, copy to runtime directory
cp ~/.hermes/hermes-agent/skills/<path>/SKILL.md \
   ~/.hermes/skills/<path>/SKILL.md
```

**Correct Workflow (verified on 2026-04-22):**

```bash
# Step 1: Edit skills in RUNTIME directory (what Hermes Agent reads)
write_file(path="~/.hermes/skills/<category>/<skill>/SKILL.md", content="...")

# Step 2: Copy to git-tracked repo (to commit changes)
mkdir -p ~/.hermes/hermes-agent/skills/<category>/<skill>/
cp ~/.hermes/skills/<category>/<skill>/SKILL.md \
   ~/.hermes/hermes-agent/skills/<category>/<skill>/SKILL.md

# Step 3: Commit from git repo
cd ~/.hermes/hermes-agent
git add skills/<category>/<skill>/SKILL.md
git commit -m "feat: ..."
```

**Why this direction:**
- `git add <path>` FAILS with "is outside repository" error when path is outside the git repo
- `~/.hermes/skills/` is NOT inside `~/.hermes/hermes-agent/` — they are sibling directories
- The git repo is `~/.hermes/hermes-agent/` (not `~/.hermes/`), so only paths inside `hermes-agent/` can be `git add`'d

**Rule:** When upgrading skills based on external research, ALWAYS edit the runtime skills directory (`~/.hermes/skills/`), then COPY to the git repo to commit. Do NOT try to `git add` paths in `~/.hermes/skills/` directly.

## Example: RIA-TV++ Skill Upgrade (Batch Process, verified 2026-04-22)

**Source:** kangarooking/cangjie-skill (444 stars, MIT, 2026-04-16) — RIA-TV++ format

**Batch upgrade workflow (5 steps):**

1. **List remaining skills** → `skills_list()` to find unupgraded skills
2. **Load current skill** → `skill_view()` to read existing content
3. **Write RIA-TV++ format** → `write_file()` to `~/.hermes/skills/<category>/<skill>/SKILL.md`
4. **Copy to git repo** → `cp` to `~/.hermes/hermes-agent/skills/<category>/<skill>/`
5. **Commit from git repo** → `cd ~/.hermes/hermes-agent && git add && git commit`

**RIA-TV++ format (6 sections):**

```yaml
---
name: <skill-name>
description: |
  <trigger language + anti-trigger>
trigger:
  - "trigger word 1"
anti_trigger:
  - "anti-trigger 1"
source: hermes-agent (adapted from cangjie-skill RIA-TV++)
version: 2.0.0  # 1.1.0 → 2.0.0 for existing skills
metadata:
  hermes:
    quality_redlines:
      - MUST have E (Execution) section
      - MUST have B (Boundary) section
      - MUST have A2 (Trigger) section
---
## A2 — 触发场景 (Trigger) ★
## R — 知识溯源 (Reading)
## I — 方法论骨架 (Interpretation)
## A1 — 实践案例 (Past Application)
## E — 可执行步骤 (Execution) ★
## B — 边界 (Boundary) ★
```

**Verification after upgrade:**
```bash
grep "version: 2.0.0" ~/.hermes/skills/<path>/SKILL.md
grep "A2 — 触发场景" ~/.hermes/skills/<path>/SKILL.md
```

## Common Pitfalls

1. **Theoretical-only projects** — Don't integrate projects that only offer concepts without implementable patterns. File for reference, don't modify skills.

2. **Redundant integration** — If two projects solve the same problem differently, pick the better format and reference both. Don't duplicate content.

3. **Over-engineering** — If a project has 50 patterns but only 2 are relevant, only integrate those 2. Don't import everything.

4. **Forgetting to commit** — Changes to skills directory must be committed same day. Use the commit format above.

5. **Breaking existing skills** — Additions only. Don't restructure existing skill content without strong justification.

6. **Editing wrong skills directory** — Use the Correct Workflow above. `git add` fails for paths outside git repo. Always copy from runtime `~/.hermes/skills/` to git repo `~/.hermes/hermes-agent/skills/` before commit.

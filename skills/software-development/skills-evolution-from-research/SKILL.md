---
name: skills-evolution-from-research
description: "Evaluate and integrate external open-source projects into Hermes Agent skills. Use when analyzing GitHub repos for potential skill improvements, or when upgrading skill standards based on external research, or when auditing existing local skills for stub quality, outdated information, or missing trigger/anti_trigger fields. NOT for: trivial one-off tasks, skills that are already well-developed and tested, when you lack environment context to validate the integration, or when the external project has no relevant overlap with existing Hermes capabilities."
category: general
version: 2.1.0
...
author: Hermes Agent
...
license: MIT
...
---

## Skill Evolution Protocol

Systematic evaluation and integration of external open-source projects into Hermes Agent skills. Follows a 4-phase process: **Audit → Research → Implement → Validate**.

---

## Critical Directory Structure

Understand the git repo layout before making changes.


~/.hermes/skills/           ← ROOT of the skills git repo (Nazicc/hermes-agent on GitHub)
  skills/                   ← "core" skills (many are stubs, <20 lines)
  optional-skills/          ← fully-developed skills (100-500+ lines)
  productivity/
  mlops/
  ...

~/.hermes/                          ← NOT a git repo (no .git here)
  skills/                            ← IS a git repo (has .git/, tracked separately)
  scripts/
  memories/
  hermes-agent/                      ← the hermes-agent git repo
    .git/
    evolver/                        ← the self-evolution evolver repo


**Critical discovery (2026-04-24)**: Most skills in `~/.hermes/skills/skills/` are stubs (~11-12 lines) with only YAML frontmatter. The real content lives in `~/.hermes/skills/optional-skills/`. Always check both paths.

### Git Operations for Skills

When using `git` on skills:
- `cd ~/.hermes/skills && git status` — not `cd ~/.hermes && git status`
- The skills repo is standalone; hermes-agent repo does NOT track skills/
- Skills are committed/pushed separately from hermes-agent code

bash
cd ~/.hermes/skills
git add skills/[name]/SKILL.md
git commit -m "feat(skills): add/evolve [name]"
git push origin main


---

## Phase 1: Audit Before Importing

Before integrating external research, audit existing local skills to identify gaps and priority targets.

### Pre-Evolution Checklist (MANDATORY)

Before touching any file, verify:

1. **Identify the correct git repo** — `~/.hermes/skills/` is often a NESTED git repo. Check with:
   bash
   ls ~/.hermes/skills/.git  # if exists, skills/ is a separate repo
   git -C ~/.hermes/hermes-agent rev-parse --is-inside-work-tree
   
   - If `skills/` has its own `.git/`, commit changes THERE, not in hermes-agent
   - If `skills/` has NO `.git/`, it may be part of hermes-agent's tree or untracked

2. **Check current git status** in the correct repo before starting:
   bash
   cd ~/.hermes/skills && git status --short | head -10
   cd ~/.hermes/hermes-agent && git status --short | head -10
   

3. **List all modified/new SKILL.md files** before committing — avoid accidentally adding unrelated changes.

4. **For SKILL.md patches**: Read the exact current description line BEFORE patching:
   bash
   head -5 skills/<name>/SKILL.md  # get exact current description
   

### Audit Commands

**Priority 1 — Stub skills (only frontmatter, no actual content):**
bash
find ~/.hermes/skills -name "SKILL.md" -not -path "*/.backup*" | xargs wc -l | sort -n | head -30

Stubs are typically 8-31 lines (mostly frontmatter, no body content).

**Priority 2 — Missing trigger/anti_trigger patterns:**
bash
find ~/.hermes/skills -name "SKILL.md" | while read f; do
  if ! head -5 "$f" | grep -q '"Use when'; then
    echo "$f"
  fi
done


**Priority 3 — Missing NOT for clause:**
bash
find ~/.hermes/skills -name "SKILL.md" | while read f; do
  if ! head -10 "$f" | grep -qi 'NOT for'; then
    echo "$f"
  fi
done


---

## Phase 2: Research External Projects

### 2.1 Discover

- Search GitHub for relevant projects using `duckduckgo-search` or direct GitHub search
- Look for patterns: agent-memory-protocol, skill-management, context-engineering
- Check both the Hermes Agent ecosystem and external AI agent projects

### 2.2 Verify

**CRITICAL: Verify external repo existence before referencing in skills**

bash
git ls-remote https://github.com/[owner]/[repo].git 2>/dev/null | head -1


If the repo doesn't exist, do NOT reference it in skills. Common false references found in audits:
- "claude-mem's mem-search skill (65k stars)" — CLAUDE-MEM DOES NOT EXIST ON GITHUB
- "obra/superpowers" — verify before referencing
- "Fission-AI/OpenSpec" — verify before referencing

### 2.3 Analyze

For each candidate external project:

1. **Clone/fetch the repo** and read SKILL.md or README in full
2. **Assess quality**: Does it have actual content (>50 lines) or is it a stub?
3. **Identify the valuable part**: Protocol design? Specific tools? API patterns? Template content?
4. **Verify against this environment**: Check if referenced APIs, ports, endpoints, or tools actually exist in `~/.hermes/` or the runtime
5. **Document findings** — use a structured comparison table:

| Dimension | External Project | Hermes Skill | Verdict |
|-----------|-----------------|--------------|----------|
| Content depth | 200 lines | 11 lines (stub) | Import content |
| API accuracy | REST endpoints listed | None | Update endpoint section |
| Environment match | Uses OpenAI API | Uses MiniMax via SkillClaw | Adapt API calls |
| Trigger quality | Has "Use when" + triggers | No triggers | Add trigger fields |

### 2.4 GEPA Automated Evaluation (Best Effort)

bash
cd /Users/can/.hermes/hermes-agent/hermes-agent-self-evolution
export OPENAI_API_KEY=...  # Required for DSPy judge
./venv/bin/python3 -m evolution.skills.evolve_skill --skill <name> --dry-run


If `venv` is missing or DSPy import fails → skip to Phase 3 (manual evolution). Do NOT try to create the venv or install DSPy.

**GEPA Pipeline (when available):**
1. **Analyze** — clone repo, extract API patterns, code examples, architectural insights
2. **Score** — DSPy judge scores: correctness, completeness, actionability, token efficiency
3. **Rank** — prioritize by gap × improvement potential
4. **Draft** — generate replacement sections
5. **Verify** — test in simulated environment

### 2.5 Synthesis

**Integration Strategy:**

- **Import content** (external is much better): Copy the core guidance sections, adapt API endpoints/ports to match this environment, preserve the structure but own the content
- **Merge** (both have value): Keep Hermes-specific paths and tool names, add external's methodological framework, combine trigger lists
- **Ignore** (not applicable): Document why in the comparison table, skip to next candidate

---

## Phase 3: Implement Locally

### 3.1 Skill Description Format (MANDATORY)

**Every skill must have this exact description format:**

yaml
description: "Use when [specific trigger situation]. [What it does]. NOT for: [explicit exclusion cases]."
trigger:
  - "trigger phrase 1"
  - "trigger phrase 2"
anti_trigger:
  - "exclusion phrase 1"
  - "exclusion phrase 2"


**Example:**
yaml
description: "Use when debugging Python crashes or unexpected behavior. 4-phase root cause investigation. NOT for: syntax errors, simple one-liners, or when you already know the fix."
trigger:
  - "debug"
  - "crash"
  - "error"
anti_trigger:
  - "syntax error"
  - "simple"


The description MUST:
1. Start with `"Use when..."` (not "Use for", not action verb)
2. Include `"NOT for:"` clause
3. Be specific enough to avoid false positives

### 3.2 Priority Categories

**Priority 1 (Critical):**
- Stub skills (only YAML frontmatter, no body content)
- Skills with fake/misleading external references
- Skills with wrong/actively harmful guidance

**Priority 2 (High):**
- Skills missing "Use when..." description format
- Skills missing trigger/anti_trigger fields
- Skills missing "NOT for:" clause

**Priority 3 (Medium):**
- Skills needing additional examples
- Skills needing updated API references
- Skills needing additional anti_trigger cases

**Priority 4 (Low):**
- Skills needing better organization
- Skills needing additional related_skill links

### 3.3 Handling Stub Discovery

**A skill is a stub if:**
1. Total file is <20 lines (excluding blank lines)
2. Description mentions "TODO" or "FIXME"
3. No `instructions:` section OR `instructions:` is empty
4. Metadata `sources:` is an empty array
5. References external projects that don't exist

**Stub rewrite protocol:**
- Read the existing stub SKILL.md
- Research the topic area from memory tools (session_search, search_memories, ask)
- Write complete guidance: ≥100 lines, concrete steps, real tool names, anti-patterns
- Preserve YAML frontmatter structure (name, description, version, author, license, metadata)
- Add `version: 1.x.0` bump on rewrite

**Stub handling:**
1. Check if it has a counterpart in `productivity/` or `optional-skills/` with full content
2. If duplicate exists with full content: DELETE the stub
3. If no counterpart: EVOLVE the stub with full content

### 3.4 Git Repository Structure (CRITICAL)

Before committing skill changes, check if the skills directory is itself a git repository:
bash
# Check if skills/ is a nested git repo
if [ -d "$SKILLS_DIR/.git" ]; then
  echo "skills/ is a git repo — commit there separately"
  cd "$SKILLS_DIR"
  git add <changed-skills>
  git commit -m "feat(skills): <description>"
  git push origin main
else
  echo "skills/ is not a git repo — parent repo commit"
fi


If you encounter `fatal: adding embedded git repository`, use:
bash
git rm --cached -f <path-to-embedded-repo>


### 3.5 Patch Tool Protocol (CRITICAL)

The patch tool requires EXACT string matching. Always read the file first to get the exact current description:
bash
read_file(path="$SKILL_PATH", limit=5)  # Get exact current frontmatter
patch(path="$SKILL_PATH", old_string="<exact string>", new_string="<new string>")


Never guess the old_string. Always read first.

### 3.6 Evolve the Skill (Step-by-Step)

For each skill being evolved:

1. **Backup original** — commit before changes so you can revert
2. **Read the current SKILL.md** — get exact frontmatter fields for patch tool
3. **Apply changes** using the patch tool with exact old_string
4. **Add missing fields** — ensure each skill has:
   - `description`: starts with "Use when..." and ends with "NOT for..."
   - `trigger`: array of activation phrases
   - `anti_trigger`: array of deactivation phrases
   - `Common Rationalizations` section: table of wrong rationalizations vs reality
5. **Verify**: Read the patched file to confirm changes persisted
6. **Commit**: `git add skills/<category>/<skill>/ && git commit -m "feat(skills): evolve <skill> from <external-project>"`

### 3.7 Target Skills Per Session

- 1 critical stub: rewrite to full content (mem-search, systematic-debugging, plan, etc.)
- 1-2 quality improvements: expand partially-written skills
- 1 cleanup: remove duplicate stubs or references to non-existent skills

---

## Phase 4: Validate

### 4.1 Validation Checklist

After integration, validate:
- Skill triggers correctly with its keywords
- Skill does NOT trigger for anti_trigger cases
- Body content is actionable and accurate
- No broken references
- Test the updated skill by checking it loads correctly
- Verify all trigger/anti_trigger patterns are unique and non-overlapping
- Check that "Use when" and "NOT for" clauses are mutually exclusive

### 4.2 Handling Git Divergence

If `git pull` reports divergence or deleted files on remote:
bash
git stash                    # save local changes
git pull --rebase origin main  # pull remote changes
git stash pop                # restore local changes
git push origin main         # push merged result


This preserves local work while accepting the remote's history rewrite.

### 4.3 Evolution Triggers

Re-evaluate a skill when:
- External project it references releases major version
- User reports it as unhelpful or misleading
- New capability makes it obsolete

---

## Known Environment Quirks

| Issue | Symptom | Fix |
|-------|---------|-----|
| skills/ is nested git repo | `git add skills/` gives embedded-repo warning | Commit to `~/.hermes/skills/` git repo directly |
| Skills in skills/skills/ are stubs | File has <20 lines | These are placeholder stubs — evolve them first |
| Patch fails silently | No error but file unchanged | Read exact current string before patching |
| hermes-agent git repo ≠ skills git repo | Changes not appearing in hermes-agent push | Check which git repo tracks the changed file |
| GEPA venv/dspy missing | ModuleNotFoundError | Perform manual evolution instead |

### Handling Embedded Git Repos

If `git add <directory>` warns about "adding embedded git repository":
bash
git rm --cached -f <directory>   # remove from index
git status                        # verify clean


The directory is a nested git repo. Work within that directory separately using `cd <directory> && git ...`.

---

## Session Sync (Evolver Bridge)

bash
cd /Users/can/.hermes/hermes-agent
./scripts/hermes_to_evolver_bridge.py --max-sessions 50


Syncs sessions from `~/.openclaw/agents/hermes-agent/sessions/` to the evolver's session store. Run at end of each self-evolution session.

**Note:** The bridge requires git history in `~/.hermes/` for git log operations. If `~/.hermes/` is not a git repo, bridge sync will fail silently or partially.

---

## AMP-Inspired Typed Memory Tools

When evolving memory-related skills, integrate AMP protocol patterns:
- Three memory types: `lesson` (learned pattern), `checkpoint` (decision state), `reflection` (self-review)
- Three-layer search: semantic index → session/timeline context → full entry fetch
- Store typed memories via `simplemem_mcp.py`: encode type in `speaker` field as `typed:{type}`

See: `~/.hermes/scripts/simplemem_mcp.py` for the AMP-typed memory implementation.

---

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just import the external repo as-is" | External repos rarely match Hermes skill format; extract only reusable patterns |
| "The GEPA evolver will handle it" | GEPA requires dspy, venv, and API keys — often unavailable; manual rewrite is the reliable fallback |
| "I'll patch all 164 skills at once" | Skills are in an embedded git repo; commit to the skills repo separately from the hermes-agent repo |
| "This skill is fine as-is" | If a skill has <20 lines, it's a stub — no amount of external research helps until the stub is rewritten |
| "External is much better, I'll copy everything" | Copy the core guidance but adapt API endpoints/ports to match this environment |

---

## Quality Standards for Evolved Skills

A well-formed skill SKILL.md has:

yaml
---
name: <skill-name>
description: |
  Use when <specific situation>. <What it does>.
  NOT for: <clear exclusion cases>.
trigger:
  - "activation phrase 1"
  - "activation phrase 2"
anti_trigger:
  - "deactivation phrase 1"
  - "deactivation phrase 2"
---


## Section 1: Core Guidance

...concrete, environment-specific instructions...

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This approach always works" | It depends on <specific condition> |

## Related Skills

- `<skill-a>` — brief relationship note
- `<skill-b>` — brief relationship note

---

## Output Format

After evolution, document:
- **Skills evolved**: list with line counts before/after
- **External sources used**: repo + specific contribution
- **Skills skipped**: reason for each
- **Git commit hash**: so the change is traceable

---

## Related Skills

- `systematic-debugging` — For investigating skill failures
- `plan` — For planning complex skill evolution tasks
- `test-driven-development` — For validating skill changes
- `spec-driven-development` — For writing specs before importing external patterns

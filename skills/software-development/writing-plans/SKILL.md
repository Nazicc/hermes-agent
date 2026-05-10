---
name: writing-plans
description: "Creates comprehensive implementation plans with bite-sized tasks, exact file paths, and complete code examples. Use when you have a spec or requirements for a multi-step task and need to break it down into executable steps. Trigger: \"write a plan\", \"create a plan\", \"implementation plan\", \"break this down\", \"how would you approach this\", \"how do I approach this\", \"how do I build\", \"where do I start\", \"plan the implementation\", \"what are the steps\", \"plan it out\", \"make a roadmap\". NOT for: simple one-step tasks, debugging (use systematic-debugging), already-detailed specs, when a plan already exists (use plan), agent self-evolution planning (use skills-evolution-from-research), emergencies, or when the user explicitly asks to just execute without planning."
category: general
---

## When to Use

- User asks "write a plan", "create a plan", "implementation plan", "break this down"
- User asks "how do I build X", "how do I approach this", "how would you approach this", "where do I start", "what are the steps"
- User has a vague goal and needs it broken into steps
- User provides a spec and expects a todo-style breakdown
- Task involves multiple files, API changes, database migrations, or new dependencies
- More than 3-5 distinct steps or reversible/risky operations

## When NOT to Use

- User is debugging → use `systematic-debugging` instead
- User wants to review/analyze an existing plan → use `plan` instead
- Task is one shell command or single file edit → just do it
- It's an emergency fix
- Agent self-evolution planning → use `skills-evolution-from-research`
- Creating specs for new projects → use `spec-driven-development`
- User explicitly says "just do it" or "execute now"

---

## Complexity Scale

| Rating | Time | Scope |
|--------|------|-------|
| XS | <10 min | Single file, no new deps |
| S | 10-30 min | 1-2 files, known stack |
| M | 30-90 min | 3-5 files, some unknowns |
| L | 90+ min | Many files, research needed |

For complexity M or L, recommend entering plan mode using the `plan` skill.

---

## Plan Directory

All plans go in `.hermes/plans/`.
Filename format: `{YYYY-MM-DD}-{short-slug}.md`

Example:


.project/.hermes/plans/
├── 2026-01-15-user-auth.md
├── 2026-01-16-payment-gateway.md
└── 2026-01-17-api-v2-migration.md


---

## Plan Structure

Every implementation plan goes into `.hermes/plans/<YYYY-MM-DD>-<slug>.md`.

### 1. Overview
One-paragraph summary of what will be built and why.

### 2. Context
Relevant background from the conversation:
- Current state of the codebase
- Constraints or requirements mentioned
- Related files or systems

### 3. High-Level Approach
2-4 sentence summary of the solution direction with key architectural decisions (file locations, data flow, external deps).

### 4. Prerequisites
- [ ] Environment requirements (Python version, Node version, etc.)
- [ ] Required credentials, tokens, or API keys
- [ ] Dependencies that need installation
- [ ] External services that need setup

### 5. Task List (Organized by Phase)

### Phase 1: Foundation (<N> tasks)
- [ ] Task 1: <Specific description with exact file paths>
- [ ] Task 2: <Specific description with exact file paths>

### Phase 2: Core Feature (<N> tasks)
- [ ] Task 3: ...
- [ ] Task 4: ...

### Phase N: Testing & Polish (<N> tasks)
- [ ] Task N: ...

### 6. File Inventory

| File | Action | Purpose | Notes |
|------|--------|---------|-------|
| `src/main.py` | CREATE | Entry point | |
| `config.yaml` | MODIFY | Add API key section | |

### 7. Verification Checklist
- [ ] Run `command --check`
- [ ] Visit `http://localhost:PORT/endpoint`
- [ ] Confirm log shows `expected message`

### 8. Rollback
If something goes wrong: `git checkout <commit> && ...`

---

## Phase Naming Convention

Use descriptive phase names:
- "Foundation" or "Setup" — project scaffolding, deps, config
- "Core Feature" — main implementation
- "Integration" — connecting components
- "Testing" — unit + integration tests
- "Polish" — edge cases, error handling, docs

Each phase should be independently verifiable. A user can run the plan and verify Phase 1 before starting Phase 2.

## Phase Decomposition Guide

| Task Type | Typical Phases |
|-----------|----------------|
| New feature | Design → Implement → Test |
| Bug fix | Reproduce → Root cause → Fix → Verify |
| Migration | Audit → Backup → Migrate → Validate |
| Setup/installation | Prerequisites → Install → Configure → Verify |

## Task Ordering Rules

1. Prerequisites and scaffolding first
2. Core logic before integration
3. Tests before edge cases
4. Integration last

---

## Task Definition Rules

**Good tasks** (actionable, verifiable):
- "Create `src/services/auth.py` with `AuthService.login()` and `AuthService.logout()` methods using JWT"
- "Add `user_preferences` table to `schema.sql` with columns: `id`, `user_id`, `key`, `value`"
- "Write integration test in `tests/test_api.py` that calls `/api/users` endpoint with mock DB"

**Bad tasks** (too vague):
- "Implement authentication"
- "Add user settings"
- "Write tests"
- "Refactor the code"

**For each task include:**
1. Exact file path(s) to create/modify
2. Specific function/class to implement (if applicable)
3. Key constraints or requirements
4. How to verify the task is done

---

## Step Writing Principles

### Bite-Sized
Each step should be:
- Completable in <10-20 minutes
- Independently verifiable
- Atomic (no partial states)

**Good**: "Update the database schema in migration 003"
**Bad**: "Refactor the entire auth system"

### Exact File Paths
Always include:
- Full relative path from workspace root
- Line number if specific
- Section name if applicable

Example: `src/handlers/auth.py:42` or `src/handlers/auth.py:validate_token(){}`

### Verification Per Step
After each step, include a verification command:

bash
# Verify: step 1
python -m pytest tests/test_auth.py -k validate_token
curl -s http://localhost:8000/health | grep ok


### Code Examples
When a step involves writing code, include the complete code:

python
# Step 3: Add token refresh logic
# File: src/handlers/auth.py:89
def refresh_token(old_token: str) -> str:
    """Refresh an expired but valid token."""
    payload = jwt.decode(old_token, options={"verify_exp": False})
    return jwt.encode({**payload, "exp": time.time() + 3600}, SECRET)


---

## Step Templates by Task Type

### New Feature
markdown
### Step N: Create <feature name>
**File(s):** `src/features/<name>.py`
**What:** Implement <feature> with <key behavior>.
**How:**
1. Add function/class in new file
2. Export from `__init__.py` if module
3. Add tests in `tests/test_<name>.py`


### API Endpoint
markdown
### Step N: Add <method> /<path> endpoint
**File(s):** `app/routes.py` or `app/api/<resource>.py`
**What:** Create endpoint that <action>.
**How:**
1. Add route handler function
2. Add request validation schema
3. Add to router/exports


### Bug Fix
markdown
### Step N: Fix <bug description>
**File(s):** `<file>:<line>`
**What:** Root cause is <issue>. Change <old> to <new>.
**How:**
python
# Before
broken_code()

# After
fixed_code()


**Verification:** Run `pytest tests/test_<module>.py::test_<case>` — should pass.


### Configuration Change
markdown
### Step N: Update <config file>
**File(s):** `<config path>`
**What:** Change `<key>` from `<old value>` to `<new value>`.
**How:**
yaml
# In <config file>
<key>: <new value>


**Rollback:** Revert to `<old value>`.


---

## Common Patterns

### Pattern: File Creation + Configuration

1. Create config file — `.env.local`
2. Add to .gitignore — `.gitignore:12`
3. Load in app — `src/config.py:8`
4. Verify — `python -c "from src.config import cfg; print(cfg.base_url)"`

### Pattern: Database Migration

1. Create migration — `migrations/004_add_users.py`
2. Run dry-run — `alembic upgrade --sql -r:004`
3. Execute — `alembic upgrade r:004`
4. Verify — `psql -c "SELECT COUNT(*) FROM users"`

### Pattern: API Endpoint Addition

1. Add route — `src/routes/api.py:45`
2. Add handler — `src/handlers/user_handler.py:12`
3. Add schema — `src/schemas.py:88`
4. Write test — `tests/test_api.py:112`
5. Verify — `curl -X POST /api/users -d '{"name":"test"}' | jq .id`

---

## Token-Saving Strategies

1. **Abbreviate repetitive sections**: Once a pattern is established (e.g., "File: .../module.py"), omit the prefix for subsequent similar steps.
2. **Reference existing patterns**: If similar code exists in the codebase, say "Follow the same pattern as `src/utils/auth.py`" instead of repeating it.
3. **Skip obvious steps**: Don't list "open the file" or "save the file" — assume standard workflow.
4. **Use tables for multi-item steps**: When a step affects multiple files, use a table instead of repeating the same structure.

---

## Common Pitfalls

| Pitfall | Prevention |
|---------|-------------|
| Planning too granular | Focus on decision points; group mechanical steps |
| Skipping prerequisites | Always list them explicitly as checkboxes |
| No rollback plan | Every non-trivial step needs one |
| Assuming knowledge | Spell out unfamiliar tool/version requirements |
| Executing in plan mode | Stop after writing the plan; wait for approval |

---

## Handling Ambiguous Requirements

When requirements are unclear:

1. **State assumptions explicitly** in the Context section
2. **Ask the user** to clarify before proceeding
3. **Provide options** with tradeoffs

markdown
## Assumptions
- [ ] We assume the database is PostgreSQL 14+
- [ ] We assume there's a `users` table already

## Options
A) Use existing auth table (faster, couples tightly)
B) Create separate tokens table (cleaner, more work)

Please confirm which approach.


---

## Hermes Plan Mode Integration

If operating in plan mode (`plan` skill active):
1. Write the plan to `.hermes/plans/`
2. **Do NOT execute any steps**
3. Present the plan to the user
4. Wait for explicit approval ("yes", "go ahead", "do it")
5. Only then execute

### Approval Gate Checklist
Before executing after plan mode approval:
- [ ] User explicitly approved
- [ ] Plan is still relevant (no major context change)
- [ ] First step is safe to start with

---

## Integration with Other Skills

- **`plan`**: For writing plans in plan mode (user approval before execution). Use `plan` skill to enter plan mode and save to `.hermes/plans/`, then use this skill to write detailed implementation steps.
- **`systematic-debugging`**: For investigating issues before planning fixes.
- **`spec-driven-development`**: For creating specs before writing plans.
- **`incremental-implementation`**: For large tasks, mark each step with `--checkpoint` comment for partial commits.

---

## Environment Notes

- Plans directory: `.hermes/plans/` (create if missing)
- Skills are in `skills/skills/<name>/SKILL.md`
- The `skills/` directory is an embedded git repository — do NOT `git add skills/` in the parent repo. Commit skill changes from within the `skills/` git repo itself.

---

## Anti-Patterns to Avoid

1. **No vague steps**: "Update stuff" or "Fix the bug"
2. **No missing verification**: Every step needs a way to confirm it worked
3. **No missing rollback**: For multi-file changes, always have a rollback plan
4. **No executing in plan mode**: If `plan` skill is active, stop at the plan
5. **Too many steps**: If a plan has >10 steps, split it. Each step should take <20 minutes.

---

## Quality Checklist

Before presenting a plan, verify:
- [ ] Every task has an exact file path
- [ ] Every task is independently verifiable
- [ ] Phase order makes logical sense (foundation before feature)
- [ ] All external dependencies are listed (npm, pip, system packages)
- [ ] Verification commands are provided for each phase
- [ ] No tasks say "implement X" without specifying where and how
- [ ] Each step has a verification command
- [ ] Steps are ordered correctly (dependencies first)
- [ ] No step is more than 10-20 minutes of work
- [ ] Rollback is documented
- [ ] Plan is saved to `.hermes/plans/`
- [ ] If in plan mode: user approval received before execution
- [ ] Every code block is complete and syntactically correct
- [ ] Cross-references between dependent steps are noted

---

## Interaction

After writing the plan:
1. Summarize it in 3-5 sentences
2. State the total number of steps and estimated complexity/risk level
3. Ask for explicit approval before executing ("Shall I proceed with Phase 1?")
4. If user approves only certain phases, execute those and stop

**Output Format**: Write the plan as a Markdown code block so the user can copy it. Use the structure above. Do not execute any steps — write the plan and stop.

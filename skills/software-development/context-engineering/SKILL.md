---
name: context-engineering
description: "Optimizes agent context setup using structured context management techniques. Use when starting a new session, when agent output quality degrades, when switching between tasks, or when configuring rules files and project context. NOT for: trivial one-off tasks, already-well-scoped implementations, or when the agent already has all necessary context."
category: general
---

## Context Engineering

Optimizes how the agent perceives, structures, and uses context throughout a session. Context is not about volume — it is about relevance, accuracy, and timely injection.

## Context Architecture

### Layers (outermost to innermost)

1. **System prompt** — static, loaded at startup; contains agent identity, capabilities, hard rules
2. **Session rules** (`~/.hermes/rules/`) — project-specific overrides, loaded per-directory
3. **Conversation history** — full transcript; subject to compression when large
4. **Working memory** — agent's active self-reflection, todo list, current focus
5. **Task context** — specific files, docs, URLs, or data relevant to current task

### Context Loading Order


system_prompt
  ↓
session_rules (per-directory .hermes/rules/)
  ↓
conversation_history (compressed if > 50 msgs)
  ↓
working_memory (from agent self-reflection)
  ↓
task_context (explicitly provided by user or retrieved)


## Context Quality Checklist

At the start of every session or when quality degrades:

- [ ] System prompt is current (not stale version)
- [ ] Session rules exist for this project (`~/.hermes/rules/`)
- [ ] Agent knows the user's identity and preferences
- [ ] Current task/goal is explicitly stated, not implied
- [ ] Relevant files or docs are accessible in task context
- [ ] Conversation history is not bloated with off-topic detours

## Phase 1 — Detect Context Degradation

Before adding more context, observe whether the problem is actually context-related:

- **Symptom**: Agent repeats itself, forgets constraints, ignores part of the request
- **Check**: Does the agent's last response show awareness of ALL provided context?
- **If yes**: The issue is NOT context — proceed with task execution
- **If no**: Context degradation confirmed — proceed to Phase 2

## Phase 2 — Audit Context Quality

Strip non-essentials before adding more:
1. Remove outdated project state references
2. Remove completed sub-task history that doesn't inform current decisions
3. Remove generic preamble that doesn't constrain behavior
4. Keep: current goal, active constraints, relevant code patterns, error state

**Do not retain more than 20 historical messages** in the active context window.

## Context Degradation Patterns

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Agent repeats itself | History too long or compressed badly | Summarize and restart subtopic |
| Agent forgets constraints | Rules not loaded or overridden | Re-state rules explicitly |
| Agent loses track of task | Context switched without summary | Inject task summary |
| Output quality drops | Context window near limit | Compress or prune history |
| Agent contradicts itself | Multiple conflicting rules loaded | Audit and deduplicate rules |

## Phase 3 — Inject Targeted Context

Add the minimum context that addresses the gap:

| Gap | Context to Add |
|-----|----------------|
| Agent doesn't know project structure | `find . -name "*.py" | head -20` + key file summaries |
| Agent ignores a constraint | State the constraint as a concrete rule |
| Agent repeats failed approaches | Log of what was tried + why it failed |
| Agent misunderstands the goal | One-sentence re-statement of the outcome |

### Context Injection Techniques

**1. Explicit Context (highest reliability)**
Always state explicitly:
- Who you are / who the user is
- What the current task is
- What the expected outcome looks like
- What constraints or preferences apply

**2. Task Framing**
At the start of a complex task:


Task: <one sentence>
Success criteria: <how we know it's done>
Constraints: <what must/must not happen>
Relevant context: <files, docs, prior decisions>


**3. Conversation Summarization**
When history exceeds ~30 messages:

Summarize the conversation so far in 3-5 bullet points.
Keep: the goal, key decisions made, remaining open questions.
Discard: failed attempts, off-topic detours, redundant explanations.

## Phase 4 — Rules Files

For recurring projects, create persistent rules in `~/.hermes/rules/<project>/`:

- `system.md` — project-specific system prompt additions
- `ignore.md` — patterns to skip (e.g., `node_modules`, `.git`)
- `preferences.md` — user preferences (language, style, tools)

Rules files should be loaded at session start, not mid-task.

### Rules File Locations

| Engine | Location |
|--------|----------|
| Hermes | `~/.hermes/rules/` |
| Claude | `.claude/` |
| Cursor | `.cursorrules` |
| Windsurf | `.windsurfrules` |

### Generating Rules Files

When rules are missing for a project:
1. Identify project type (Python/JS/Rust/etc.)
2. Extract project specs (README, package.json, pyproject.toml)
3. Generate project-level rules for identity, conventions, and preferences

**Rules must use relative paths**, not absolute paths.

## BDI Mental Models (for Multi-Agent Context)

When the agent acts as a proxy for other agents or services:

- **Beliefs** — what the agent currently believes about the world (from context)
- **Desires** — what the agent wants to achieve (from task + user goals)
- **Intentions** — what the agent decides to do next (from planning)

Re-evaluate BDI state when:
- New information contradicts a belief
- A sub-goal is achieved or abandoned
- The user changes the task

## Success Criteria

- Agent's first output aligns with project conventions
- No "skipping steps" (omitting intermediate steps)
- Output format and style match project standards

## Failure Signals

| Signal | Cause |
|--------|-------|
| Agent repeats previously stated content | Context pollution not cleared |
| Agent unaware of project conventions | Rules not correctly injected |
| Output is incoherent | Context too large, needs compression |

## Execution Boundaries

**Must follow:**
- Do not modify project source code unless explicitly requested
- Do not overwrite existing user rules files
- Use native context injection mechanisms
- Record all files found during audit for cleanup reference

**Prohibited:**
- Injecting sensitive information (API keys, tokens, passwords)
- Including absolute paths in rules files
- Retaining excessive historical messages (>20 active)

## Common Rationalizations

| Rationalization | Reality |
|----------------|----------|
| "Context is fine as-is" | If output quality has degraded, audit and clean — don't assume |
| "More context is better" | Irrelevant context dilutes relevant signals — quality beats quantity |
| "I'll just dump all files in context" | Token limits mean quality beats quantity — add only relevant context |
| "The agent should know the project by now" | Each session starts fresh — don't assume prior context |
| "I'll add context as I go" | Proactive context setup at session start avoids mid-task degradation |
| "I'll just restart the session" | Restarting loses working context — only restart when pollution is severe |
| "Fresh starts lose accumulated context" | Summarization preserves context — don't waste it |
| "The system prompt covers everything" | System prompts are static; context degrades from conversation |
| "I told it once, it should remember" | The agent's context window is limited; repetition is necessary |
| "Rules files are optional" | Without rules, Agent invents conventions inconsistent with project |
| "I can infer the project structure" | Inference is error-prone — explicit rules are faster and correct |
| "Context management is the user's job" | Agent is responsible for maintaining its own context quality |

## Relationship to Other Skills

- **`planning-with-files`** — use file-based planning for complex multi-session tasks
- **`systematic-debugging`** — if context degradation causes bugs, debug the context first
- **`spec-driven-development`** — specs are a form of task context; load them early

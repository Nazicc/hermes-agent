---
name: skill-evolution-principles
description: >
  Principles and practices for evolving AI agent skills from real session data.
  Covers the complete loop: session capture → evidence extraction → skill improvement
  → verification → deployment. For use after SkillClaw's evolver generates new skill
  content, or when manually updating skills based on observed failures.
  NOT for: writing skills from scratch without session evidence.
trigger:
  - "evolve skill"
  - "skill improvement"
  - "update skill"
  - "skill quality"
  - "skill evidence"
  - "skill feedback"
  - "技能进化"
  - "优化技能"
anti_trigger:
  - "write a new skill from scratch"  # use idea-refine for new skills
  - "不需要验证"  # skipping verification is not acceptable
version: 1.0.0
license: MIT
metadata:
  sources:
    - AMAP-ML/SkillClaw: evolve_server/pipeline/execution.py (evolve_skill_from_sessions)
    - AMAP-ML/SkillClaw: evolve_server/pipeline/skill_verifier.py
    - AMAP-ML/SkillClaw: evolve_server/pipeline/summarizer.py
    - AMAP-ML/SkillClaw: evolve_server/pipeline/session_judge.py
  hermes:
    tags: [skill-evolution, skill-quality, session-analysis, PRM, skill-verification, collective-learning]
    related_skills: [systematic-debugging, hermes-evolver-integration]
---

## The Skill Evolution Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────┐  │
│  │  Session │ ──► │  Summarize   │ ──► │  Aggregate  │ ──► │  Evolve  │  │
│  │  Data    │     │  (trajectory │     │  (by skill │     │  (edit / │  │
│  │          │     │  + analysis) │     │  reference) │     │  create) │  │
│  └──────────┘     └──────────────┘     └─────────────┘     └────┬─────┘  │
│                                                                    │        │
│                         ▲                                         ▼        │
│                         │           ┌─────────────┐     ┌────────────┐    │
│                         └──────────── │  Verify    │ ◄── │   Skill    │    │
│                                      │ (conserva- │     │  Quality   │    │
│                                      │  tive gate)│     │  Gate      │    │
│                                      └─────────────┘     └────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key principle from SkillClaw (execution.py):**
> The CURRENT skill is the source of truth. Default to targeted edits, not rewrites.
> If the session evidence shows the skill is wrong or missing something, fix THAT specific section.

---

## Principle 1 — Evidence Before Editing

**Never edit a skill without session evidence. Never edit based on a single failure.**

| Evidence Quality | Action |
|-----------------|--------|
| 0-1 failure, no pattern | Monitor only |
| 2-3 failures, same section | Targeted edit to that section |
| 5+ failures across sections | Broader improvement, but stay targeted |
| 1 failure, but CRITICAL (wrong API, wrong path) | Immediate targeted fix |

**What counts as evidence:**
- Session trajectories (exact tool calls + outcomes)
- LLM-generated session analysis
- PRM (Process Reward Model) scores per turn
- Agent-observable errors (tool failures, timeouts)

---

## Principle 2 — Preserve Skill Value

**The most important rule: do NOT delete correct environment-specific information.**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  HARD CONSTRAINT                                                        │
│                                                                         │
│  If a skill contains correct environment facts (API endpoints,        │
│  ports, payload formats, file paths, tool names) and the agent         │
│  failed because it DIDN'T use that information — that is an            │
│  AGENT problem, NOT a skill problem.                                   │
│                                                                         │
│  DO NOT delete the correct API information from the skill and replace   │
│  it with instructions like "go read utils.py".                          │
│                                                                         │
│  The whole point of the skill is to save the agent from having to       │
│  rediscover that information.                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Principle 3 — Distinguish Failure Types

Before editing a skill, classify the failure:

```
┌──────────────────────────────────────────────────────────────────────┐
│  SKILL FAILURE (edit the skill)                                       │
│                                                                      │
│  The skill was WRONG, MISSING, or MISLEADING for this environment.   │
│  → Fix the specific section that caused the failure                  │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  AGENT FAILURE (do NOT edit the skill)                               │
│                                                                      │
│  The agent misread or ignored correct skill guidance.                 │
│  → The skill already has correct info — improve agent process        │
│  → DO NOT delete correct information from the skill                   │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  ENVIRONMENT FAILURE (add brief caveat)                               │
│                                                                      │
│  Environment behaves unexpectedly (flaky mock, timing issues).       │
│  → Add brief note about known instability (1-2 sentences max)         │
│  → Do NOT add retry loops, retry tutorials, or excessive handling    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Principle 4 — Conservative Editing Mode

**Default to preserving structure. Only restructure when evidence demands it.**

```
DO:
  ✓ Tighten or clarify an existing section
  ✓ Add a specific checklist item tied to an observed failure
  ✓ Add missing environment-specific details (endpoints, paths, commands)
  ✓ Preserve original section headings and ordering
  ✓ Preserve terminology used in successful sessions

DO NOT:
  ✗ Rewrite an entire skill from scratch
  ✗ Impose a new mandatory template or section structure
  ✗ Add generic best-practice guidance the agent already knows
  ✗ Change task API contracts without evidence they changed
  ✗ Turn the skill into a tutorial or failure postmortem
  ✗ Add generic retry logic, caching strategies, or state management
    unless the specific environment requires it
```

---

## Principle 5 — Skill Verification Gate

**Before publishing any evolved skill, verify it meets these criteria:**

```
VERIFICATION CHECKLIST (from skill_verifier.py):

Grounded in Evidence:
  □ At least 2+ sessions support this change
  □ The change addresses a specific, recurring pattern
  □ The change is specific to this environment, not generic advice

Preserves Existing Value:
  □ Correct API endpoints, ports, paths preserved (if any existed)
  □ Existing effective guidance preserved
  □ Nothing removed without justification

Specificity and Reusability:
  □ The skill teaches the agent something it can't easily discover
  □ The guidance is concrete (specific file paths, exact commands)
  □ NOT generic "best practices" the agent should already know

Safe to Publish:
  □ The skill does not introduce new wrong information
  □ The trigger (description) is accurate — not over/under-triggering
  □ The change is better than the current version
```

**Minimum score threshold: 0.75/1.0** — if verification score < 0.75, keep as local draft.

---

## Principle 6 — Skill Description Quality

**The description is the trigger. Bad description = wrong skill matched to tasks.**

Good description structure (2-4 sentences):
```
Use when: <specific situation + what to do>
NOT for: <common misuses — what this skill is NOT for>
```

```
Example GOOD description:
  "Use when reading a SKILL.md file to understand its trigger conditions,
  metadata fields, and how to load the skill. NOT for: writing new skill
  files from scratch (use idea-refine), or understanding skill file
  structure in the abstract."

Example BAD description:
  "Manages skills."  (too vague — will trigger on every task)
  "Use when you need to do anything with files."  (way too broad)
```

---

## Principle 7 — Session Evidence Format

When documenting why a skill was evolved, include this evidence block:

```markdown
## Evolution Evidence

**Trigger**: <what prompted the evolution>
**Sessions analyzed**: <count>
**Key pattern**: <what the sessions showed>
**Change made**: <specific edit>
**Verification**: <how it was verified>
```

---

## Principle 8 — PRM Score Interpretation

**PRM (Process Reward Model) scores guide what needs evolution:**

| PRM Pattern | Interpretation | Action |
|-------------|---------------|--------|
| High scores (0.8+) across sessions | Skill working well | No change needed |
| Low scores (0.3-) on specific sections | Targeted guidance missing | Edit that section |
| Mixed scores across sessions | Inconsistent performance | Investigate which tasks trigger poorly |
| Score drops at specific step N | Step N guidance gap | Add specificity to step N |

**PRM scoring dimensions:**
- task_completion: 55% weight — did the goal get achieved?
- response_quality: 30% weight — correctness + completeness
- efficiency: 5% weight — avoid unnecessary retries/detours
- tool_usage: 10% weight — appropriate tool selection

---

## Anti-Rationalization Table

| Rationalization | Reality |
|-----------------|---------|
| "The skill is old, let's rewrite it" | Evidence should drive rewrites, not age |
| "I'll add comprehensive retry handling" | Generic retry logic bloats skills — only add if env requires it |
| "This skill should work for everything" | Overly broad skills don't trigger on anything specific |
| "One failure proves the skill is wrong" | One failure needs investigation, not rewrite |
| "The agent clearly didn't read the skill" | If the info was there and agent missed it, agent needs better process |
| "I'll add a section on debugging this" | Don't teach debugging IN the skill — use systematic-debugging skill |

---
name: systematic-debugging
description: >
  Use when encountering any bug, test failure, or unexpected behavior. 4-phase root
  cause investigation — gather evidence BEFORE forming hypotheses, distinguish skill failures
  from agent failures from environment failures. NO fixes without understanding.
  NOT for: simple typo fixes, one-liner corrections, or when the problem is already isolated.
trigger:
  - "debug"
  - "bug"
  - "failing"
  - "error"
  - "crash"
  - "not working"
  - "调试"
  - "报错"
  - "unexpected"
anti_trigger:
  - "typo"  # simple typo fixes need no debugging
  - "formatting"  # formatting issues need no root cause analysis
version: 2.0.0
license: MIT
metadata:
  sources:
    - SkillClaw: session_judge.py — "Distinguishing skill problems from agent problems from environment problems"
    - addyosmani/agent-skills: debugging-and-error-recovery
  hermes:
    tags: [debugging, troubleshooting, problem-solving, root-cause, investigation, triage]
    related_skills: [test-driven-development, skill-evolution-principles]
---

## 4-Phase Debugging Protocol

### Phase 1 — Triage: Classify the Failure Type

Before writing any code or changing anything, determine WHAT KIND of failure you are facing.
**This is the most critical step — wrong classification leads to wrong fixes.**

```
┌─────────────────────────────────────────────────────────────────────┐
│  CLASSIFICATION MATRIX                                              │
│                                                                      │
│  Is the failure reproducible?                                         │
│    NO  → Environment issue (flaky, race, timing) → document & retry   │
│    YES → Continue below                                              │
│                                                                      │
│  Did you recently CHANGE this code and it broke?                     │
│    YES → Revert first, then re-introduce changes incrementally      │
│    NO  → Continue below                                              │
│                                                                      │
│  Did a SKILL give you WRONG or MISSING guidance that caused this?   │
│    YES → Skill failure → update the skill                           │
│    NO  → Continue below                                               │
│                                                                      │
│  Is this a recurring agent-level mistake (misread, wrong tool,       │
│  context overflow, subagent misuse)?                                 │
│    YES → Agent failure → improve your process, NOT the skill         │
│    NO  → Continue below                                              │
│                                                                      │
│  Is the skill MISSING guidance for this specific environment?        │
│    YES → Environment knowledge gap → extend skill with specifics      │
│    NO  → Unknown cause → gather more evidence                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase 2 — Gather Evidence (Zero Assumption Mode)

**CRITICAL: Do not form hypotheses yet. Collect facts first.**

For each failure, collect ALL of:
- Exact error message (copy the full traceback)
- Command that triggered it
- Expected behavior vs actual behavior
- Environment: OS, versions, tool versions
- Whether it reproduces on retry
- Whether other similar tasks work
- Relevant skill(s) that were loaded during failure

```
Evidence template:
  Error: <exact error message>
  Command: <what you ran>
  Expected: <what should happen>
  Actual: <what happened>
  Environment: <OS, versions>
  Reproducible: <yes/no/sometimes>
  Skills loaded: <list>
  Similar tasks: <work/fail>
```

### Phase 3 — Root Cause (Hypothesis Formation + Testing)

**Only now form hypotheses, ONE AT A TIME.**

```
FORM → TEST → CONFIRM/REJECT → REPEAT

Wrong approach:
  "I'll try X, Y, and Z and see which one works"

Right approach:
  "I think the bug is A because B evidence. Let me test A."
  [test]
  [confirmed] → Fix only A, then verify
  [rejected]  → Log evidence, form new hypothesis
```

**Priority order for hypothesis testing:**
1. Simplest explanation first (typo, wrong path, missing dependency)
2. Most recent change (revert → test → re-introduce)
3. Skill guidance issue (read the relevant skill again carefully)
4. Environment-specific quirk (read the environment docs/configs)
5. Complex interaction (only after simple causes ruled out)

### Phase 4 — Fix + Verify

**Fix only the confirmed root cause. Do not refactor adjacent code.**

```
FIX:
  1. Fix ONLY the confirmed root cause
  2. Write a test that would have caught this bug
  3. Run the test → must pass
  4. Run full regression suite

VERIFICATION CHECKLIST:
  □ Bug reproduces with exact original conditions
  □ Fix resolves the bug
  □ Test(s) written and passing
  □ No new warnings or errors introduced
  □ Adjacent functionality unaffected
```

---

## The Skill Problem vs Agent Problem Distinction

**From SkillClaw's session_judge (execution.py):**

This is the most important insight for debugging in an AI agent context.

```
┌────────────────────────────────────────────────────────────────┐
│  SKILL FAILURE (fix the skill)                                  │
│                                                                │
│  The skill guidance was WRONG, MISSING, or MISLEADING.         │
│  Examples:                                                      │
│  - Skill said "use endpoint X" but endpoint X doesn't exist    │
│  - Skill omitted critical step (e.g., "install dependencies")  │
│  - Skill described wrong behavior for this specific env        │
│  → Fix: Update the skill with correct environment knowledge    │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  AGENT FAILURE (do NOT bloat the skill)                        │
│                                                                │
│  The agent misread, misused, or ignored correct skill guidance. │
│  Examples:                                                      │
│  - Skill correctly said "use endpoint X" but agent used Y      │
│  - Agent didn't read the skill before acting                    │
│  - Agent made wrong tool choice despite correct guidance        │
│  - Agent introduced a bug in code UNRELATED to skill scope      │
│  → Fix: Improve agent process, NOT the skill                   │
│  → The skill already has correct info — the problem is the      │
│    agent not following it. Don't delete correct info.           │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  ENVIRONMENT FAILURE (extend the skill with caveats)           │
│                                                                │
│  The environment is unstable or behaves unexpectedly.           │
│  Examples:                                                      │
│  - Mock API returns random errors or timeouts                  │
│  - Docker container starts slowly/flakily                       │
│  - Network connection drops intermittently                      │
│  → Fix: Add brief note about known instability, keep it short   │
│  → Do NOT turn the skill into a retry tutorial                  │
└────────────────────────────────────────────────────────────────┘
```

---

## Anti-Rationalization Table

These are the excuses agents use to skip proper debugging. Recognize them and reject:

| Rationalization | Reality |
|-----------------|---------|
| "It's probably just a typo" | If you don't know, you haven't debugged yet |
| "I'll just try X and see if it works" | That's not debugging, that's guessing |
| "The error is clear enough" | No error message tells you its own cause |
| "I understand the codebase well enough" | The bug exists precisely where your understanding gaps |
| "This worked before in similar code" | Different context = different behavior |
| "Let me just Google it and apply the first answer" | Stack Overflow answers are not debugging |
| "The test probably has a bug, not my code" | First prove your code correct, then question the test |
| "I don't have time to debug properly" | Wrong fix costs more time than right fix |

---

## Red Flags (Stop Immediately and Reassess)

- You formed a hypothesis before collecting all evidence
- You applied multiple fixes before running any test
- You "fixed" something by deleting error messages instead of fixing the cause
- The error message mentions a line number but you didn't look at that line
- You're changing code outside the module where the error originates
- A fix removes error handling rather than correcting the error condition

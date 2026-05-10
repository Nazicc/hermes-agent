---
name: spec-driven-development
description: "Spec-driven development (SDD) for AI coding assistants — inspired by OpenSpec (Fission-AI/OpenSpec). Use when starting a new project, feature, or significant change and no specification exists yet. Use when requirements are unclear, ambiguous, or only exist as a vague idea. Use when multiple stakeholders have conflicting expectations or the technical approach is not obvious. Integrates with writing-plans, incremental-implementation, and test-driven-development. NOT for: well-specified tasks, exploratory prototyping, hotfixes under time pressure, one-off scripts, incremental bugfixes, or when moving fast is more important than alignment."
category: general
---

## Core Philosophy

fluid not rigid → iterative not waterfall → easy not complex →
built for brownfield not just greenfield → scalable from personal projects to enterprises

Every non-trivial change goes through a structured artifact pipeline before any code is written.

---

## When to Use SDD

**Appropriate when:**
- No specification exists yet for the feature or change
- Requirements are unclear, ambiguous, or only exist as vague ideas
- Multiple stakeholders have conflicting expectations
- The technical approach is not obvious
- Significant architectural decisions need to be made
- You want to prevent rework by aligning on scope first

**NOT appropriate when:**
- Requirements are already clear and stable
- The change is a well-defined bugfix
- You need to move fast and the cost of misalignment is low
- The task is trivial (one-liner, obvious rename, etc.)
- Exploratory prototyping (use iterative approaches instead)
- Hotfixes under time pressure
- Incremental bugfixes with existing test coverage

---

## Artifact Pipeline

IDEA → PROPOSAL → SPECS → DESIGN → TASKS → IMPLEMENT → REGRESSION → VERIFY → LAUNCH

Each artifact has explicit dependencies — later artifacts cannot be created before earlier ones are complete.

---

## Directory Structure

SPEC/
├── proposal.md          # Phase 1 output
├── specs/
│   ├── 001-feature.md    # One spec per logical piece
│   ├── 002-api.md
│   └── 00N-feature.md
├── design.md             # Phase 3 output
├── tasks.md              # Phase 4 output
└── verify.md             # Phase 7 output

---

## Phase 1: Proposal

**File**: `SPEC/proposal.md`

Answer the "why" before the "what":

markdown
# Proposal: <short title>

## Problem Statement
What problem does this solve? Why does it matter now?

## Success Criteria
How do we know this succeeded? (measurable outcomes)

## Scope
What is in scope? What is explicitly out of scope?

## Constraints
What are the boundaries? Budget, time, tech stack, SLAs.

## Risks
What could go wrong? What are the unknowns?

## Alternatives Considered
What else was considered? Why was this approach chosen?

## Rollback Plan
How do we undo this if it goes wrong?

## Stakeholders
Who cares about this? Who approves?


**Do Not Proceed to Specs Without**:
- [ ] Problem statement that a reasonable engineer would call "specific"
- [ ] At least one concrete success criterion
- [ ] Risks identified (even if mitigation is TBD)
- [ ] Rollback plan documented

---

## Phase 2: Specifications

**File**: `SPEC/specs/<feature-name>.md` (one file per logical feature)

Answer: **What exactly will we build?**

markdown
# Spec: <feature name>

## Overview
One-paragraph summary of what this feature does.

## Functional Requirements

### FR-1: <requirement title>
**Given** [precondition]  
**When** [action]  
**Then** [observable outcome]

### FR-2: ...

## Non-Functional Requirements
- Performance: ...
- Security: ...
- Compatibility: ...

## Data Structures

### Type: [Name]
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Primary key |

## Error Handling

| Condition | Behavior |
|-----------|----------|
| Invalid input | Return 400 with details |

## Edge Cases
- EC-1: <case> → <behavior>
- EC-2: ...

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2


**Rule**: Specs must be concrete and verifiable. "The system should be fast" is not a spec. "Response time < 200ms at P99 under 1000 RPS" is.

**Do Not Proceed to Design Without**:
- [ ] Every core feature has a Gherkin-style acceptance criterion
- [ ] Error conditions enumerated
- [ ] Data structures defined with field-level precision
- [ ] Edge cases explicitly listed

---

## Phase 3: Technical Design

**File**: `SPEC/design.md`

Answer: **How will we build it?**

markdown
# Design: <title>

## Architecture
[Diagrams, ASCII art, or text description of the architecture]

## Component: [Name]

### Responsibility
What this component owns and does.

### Public API

#### `method_name(params) -> ReturnType`
**File:** `src/path/to/file.py`
**Description:** [1 sentence]

## Data Flow
[How data moves through the system]

## Dependencies
- External: [list]
- Internal: [list]
- Configuration: [list]

## Security Considerations
- Input validation
- Auth/authz
- Data handling
- Secrets management

## Cross-Platform Concerns
- macOS / Linux / Windows differences
- Browser compatibility (if applicable)

## Migration / Backward Compatibility
How does this change affect existing users? Is migration required?


**Rule**: Design must specify the "how" with enough detail that a developer could implement it without asking further questions. "Use a cache" is not a design. "Use an in-memory LRU cache with 1000-entry limit and TTL of 5 minutes, evicted on process restart" is.

**Do Not Proceed to Tasks Without**:
- [ ] Architecture clearly described
- [ ] Every component has a defined responsibility
- [ ] Security considerations addressed
- [ ] Complex logic has code examples or detailed descriptions

---

## Phase 4: Implementation Tasks

**File**: `SPEC/tasks.md`

Answer: **Exactly what do we do, in what order?**

markdown
# Tasks: <title>

## Task Ordering Principles
1. **Foundation first**: Infrastructure, types, interfaces before implementations
2. **Dependency order**: If B depends on A, A is Task 1
3. **Thin slices**: Each task should be independently testable

## Task Checklist

### Task 1: [Short Title]
**Spec Reference:** `SPEC/specs/00X-feature.md`
**Design Reference:** `SPEC/design.md#component-name`

#### Steps
1. [File: `path/to/file.ext`]
   
   [exact code or diff]
   
2. [Verify]
   bash
   command to verify
   

#### Verification
- [ ] Command X passes
- [ ] Output contains Y

---

### Task 2: [Short Title]
...


**Rule**: Tasks must be small enough to complete in a single session (< 2 hours). If a task is larger, break it down.

**Do Not Proceed to Implementation Without**:
- [ ] Every spec item mapped to a task
- [ ] Task ordering respects dependencies
- [ ] Each task has a verification command

---

## Phase 5: Implementation

### Per-Task Discipline

1. **Read** the task. Only the task.
2. **Verify preconditions** (does the file exist? is the dependency done?)
3. **Implement** exactly what the task says
4. **Verify** with the command in the task
5. **Commit** after each successful task

### Code Rules

- Zero tolerance for TODO comments in code — either do it or file an issue
- No commented-out dead code — delete it
- All new code must pass linting before commit
- Type signatures must be explicit (no `any` without documentation)

### Commit Format


<type>(<scope>): <short description>

[TASK-N] Short description

- What changed
- Why it was necessary
- How it was verified


Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

**Do Not Skip**:
- [ ] Running the verification command for each task
- [ ] Committing after each successful task

---

## Phase 6: Regression Tests

**Before marking any feature complete**, run the full regression test suite.

**Definition**: A regression test is any test that verifies existing, unchanged functionality still works.

markdown
# Regression Test Checklist

## Smoke Tests
- [ ] Core build succeeds: `make build` / `pnpm build` / etc.
- [ ] All unit tests pass: `make test` / `pnpm test` / etc.
- [ ] No new lint errors introduced

## Integration Tests (if applicable)
- [ ] API contracts still honored
- [ ] Database migrations run cleanly
- [ ] Auth flows unchanged

## Feature-Specific Regression
- [ ] Existing users can still do X (from previous specs)
- [ ] No performance regression on key paths

## Manual Verification (if no automated test exists)
- [ ] Feature X manually tested on [platform]
- [ ] Edge case Y manually verified


bash
# Run the full test suite
pytest tests/ -v

# Run integration tests
pytest tests/integration/ -v


**Rule**: If the regression test suite has ANY failures after your change, you cannot proceed to launch until they are fixed or explicitly waived with a documented reason.

---

## Phase 7: Verification

**File**: `SPEC/verify.md`

**Before launch**, perform a final verification sweep:

markdown
# Launch Verification Checklist

## Correctness
- [ ] No `console.error` or unhandled exceptions in code paths
- [ ] All error cases have user-friendly messages
- [ ] Input validation covers all edge cases from the spec
- [ ] No hardcoded secrets, credentials, or API keys

## Testing Coverage
- [ ] New code has unit test coverage ≥ 80% (or documented exception)
- [ ] All acceptance criteria from spec are covered by tests
- [ ] Edge cases from spec are tested

## Performance
- [ ] No obvious N+1 queries (if database is involved)
- [ ] No synchronous operations that could block the event loop (Node.js)
- [ ] Startup time unchanged (if applicable)

## Security
- [ ] No SQL injection vectors
- [ ] No XSS vectors
- [ ] Auth tokens not logged
- [ ] File paths sanitized (especially on Windows)

## Compatibility
- [ ] Works on all supported platforms (macOS, Linux, Windows)
- [ ] No regression for existing users

## Rollback
- [ ] Rollback plan from proposal is documented and tested
- [ ] Migrations are reversible (or marked as one-way with justification)

## Pre-Launch
- [ ] All tasks completed
- [ ] Documentation updated
- [ ] Code review approved


---

## Phase 8: Launch

**Pre-launch**:
1. Final verification checklist complete
2. Regression tests green
3. Code review approved
4. Changelog updated
5. Version bumped (if applicable)

**Launch execution**:
bash
# Verify everything is clean
make test && make build && echo "Ready to deploy"

# For infrastructure changes — dry run first
terraform plan -out=plan.tfplan

# Deploy with rollback capability
./scripts/deploy.sh --rollback-on-failure


**Post-launch**:
- Monitor error rates for 30 minutes
- Verify success criteria from proposal are being met
- Update proposal with actual outcomes

---

## Gate Criteria

Before moving to implementation, verify:

- [ ] Proposal clearly states the problem
- [ ] Each spec has at least one testable acceptance criterion
- [ ] Design identifies all files to be created/modified
- [ ] Tasks are in dependency order
- [ ] No spec contradicts another

---

## Anti-Patterns (Do NOT Do)

1. **Spec after code** — Writing the spec *after* writing the code defeats the purpose. The spec must exist before code.
2. **Vague acceptance criteria** — "Works correctly" is not acceptance criteria. Be measurable.
3. **Skipping regression tests** — "The change is small, it won't break anything" — it will.
4. **No rollback plan** — Every non-trivial change needs a rollback plan in the proposal.
5. **Implementing outside the spec** — If you found something the spec missed, update the spec first.
6. **Skipping design for "simple" changes** — Most bugs come from "simple" changes that weren't fully thought through.

---

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The idea is simple enough, we don't need a spec" | Simple ideas produce complex implementations without specs — the spec forces you to think it through |
| "I'll write the spec as I go" | This produces no spec. Specs require dedicated, uninterrupted thinking time before coding begins |
| "The user just wants a quick prototype" | Prototypes become production. Writing a spec for a prototype costs 30 minutes and saves days of refactoring |
| "I know what needs to be built" | Knowing and documenting are different activities. If it's not documented, it's not agreed upon |
| "We can fill in the details during implementation" | Implementation details reveal spec gaps — but finding them mid-implementation is 10x more expensive than before coding starts |
| "The existing codebase is the spec" | Code describes what the system does, not what it should do. Only a spec answers "should we change this?" |
| "Specs go out of date" | Unmaintained specs become wrong. Maintained specs are living documents — update them during implementation |
| "Writing specs slows us down" | Specs slow down bad implementations and accelerate good ones. The upfront cost is amortized across the entire project lifetime |
| "I'll remember all the edge cases" | You won't. The spec documents them so you don't have to hold them all in memory |
| "The code review will catch spec gaps" | Code reviews catch code quality issues. Spec gaps are found by QA, users, or production incidents — the most expensive places |
| "We don't have time to write a spec" | You don't have time NOT to write a spec. A 2-hour spec prevents 2-week refactors |
| "This is just a small change" | Small changes have an uncanny tendency to become large changes. Spec it before the scope expands |

---

## Quick Reference

| Phase | File | Question Answered | Do Not Proceed If |
|-------|------|-------------------|-------------------|
| Proposal | `SPEC/proposal.md` | Why? What problem? | No problem statement, no success criteria, no rollback plan |
| Specs | `SPEC/specs/*.md` | What exactly? | No concrete acceptance criteria, no edge cases |
| Design | `SPEC/design.md` | How? | No implementation detail, no security review |
| Tasks | `SPEC/tasks.md` | In what order? | Task ordering violates dependencies |
| Implement | — | — | Task not verified, linting fails |
| Regression | — | Did we break existing? | Any test failure |
| Verify | `SPEC/verify.md` | Is it truly done? | Any checklist item unmet |
| Launch | — | — | Verification incomplete |

---
name: spec-driven-development
description: >-
  Spec-driven development (SDD) for AI coding assistants — inspired by OpenSpec (Fission-AI/OpenSpec).
  Use when starting a new project, feature, or significant change and no specification exists yet.
  Use when requirements are unclear, ambiguous, or only exist as a vague idea.
  Integrates: proposal → specs → design → tasks → implement → regression tests → bug-free verify → launch.
trigger:
  - spec
  - specification
  - SDD
  - "write a spec"
  - "before code"
  - "no spec"
  - "requirements are unclear"
anti_trigger:
  - debugging
  - "quick fix"
  - "typo"
source: hermes-agent
version: 3.1.0
license: MIT
metadata:
  hermes:
    tags: [spec, specification, SDD, OpenSpec, development, proposal, design, tasks, regression, launch]
    related_skills: [test-driven-development, systematic-debugging, writing-plans, incremental-implementation, requesting-code-review]
---

# Spec-Driven Development (SDD)

Inspired by [OpenSpec](https://github.com/Fission-AI/OpenSpec) — an AI-native spec-driven development framework.

## Core Philosophy

```
fluid not rigid → iterative not waterfall → easy not complex →
built for brownfield not just greenfield → scalable from personal projects to enterprises
```

Every non-trivial change goes through a structured artifact pipeline before any code is written.

---

## Artifact Pipeline

```
proposal.md → specs/*.md → design.md → tasks.md → IMPLEMENT → REGRESSION → VERIFY → LAUNCH
```

Each artifact has explicit dependencies — later artifacts cannot be created before earlier ones are complete.

---

## Surface Assumptions First

Before writing any spec content, **always surface your assumptions**:

```
ASSUMPTIONS I'M MAKING:
1. This is a web application (not native mobile)
2. Authentication uses session-based cookies (not JWT)
3. The database is PostgreSQL (based on existing Prisma schema)
4. We're targeting modern browsers only (no IE11)
→ Correct me now or I'll proceed with these.
```

Don't silently fill in ambiguous requirements. The spec's entire purpose is to surface misunderstandings *before* code gets written — assumptions are the most dangerous form of misunderstanding.

---

## Phase 1: Proposal

**File**: `SPEC/proposal.md`

Answer the "why" before the "what":

```markdown
# Proposal: <short title>

## Problem
What problem does this solve? Why does it matter now?

## Success Criteria
How do we know this succeeded? (measurable outcomes)

## Scope
What is in scope? What is explicitly out of scope?

## Alternatives Considered
What else was considered? Why was this approach chosen?

## Rollback Plan
How do we undo this if it goes wrong?
```

**Rule**: A proposal with no clear problem statement and success criteria is incomplete. Do not proceed to specs.

---

## Phase 2: Specifications

**File**: `SPEC/specs/<feature-name>.md` (one file per logical feature)

### Reframe Instructions as Success Criteria

When receiving vague requirements, translate them into concrete conditions:

```
REQUIREMENT: "Make the dashboard faster"

REFRAMED SUCCESS CRITERIA:
- Dashboard LCP < 2.5s on 4G connection
- Initial data load completes in < 500ms
- No layout shift during load (CLS < 0.1)
→ Are these the right targets?
```

This lets you loop, retry, and problem-solve toward a clear goal rather than guessing what "faster" means.

### Six Core Spec Areas

```markdown
# Spec: [Project/Feature Name]

## Objective
[What we're building and why. User stories or acceptance criteria.]

## Tech Stack
[Framework, language, key dependencies with versions]

## Commands
[Build, test, lint, dev — full commands]

## Project Structure
[Directory layout with descriptions]

## Code Style
[Example snippet + key conventions]

## Testing Strategy
[Framework, test locations, coverage requirements, test levels]

## Boundaries
- Always: [...]
- Ask first: [...]
- Never: [...]

## Success Criteria
[How we'll know this is done — specific, testable conditions]

## Open Questions
[Anything unresolved that needs human input]
```

Functional requirements use Gherkin-style:

```
### FR-1: <requirement title>
**Given** [precondition]
**When** [action]
**Then** [observable outcome]
```

**Rule**: Specs must be concrete and verifiable. "The system should be fast" is not a spec. "Response time < 200ms at P99 under 1000 RPS" is.

---

## Phase 3: Technical Design

**File**: `SPEC/design.md`

```markdown
# Design: <title>

## Architecture
[Diagrams, ASCII art, or text description of the architecture]

## Data Model
[Schema, ER diagram, or data structures]

## API Design (if applicable)
[Endpoints, request/response shapes, error codes]

## Dependencies
[- External services / libraries
- Internal modules
- Configuration changes]

## Security Considerations
[- Input validation
- Auth/authz
- Data handling
- Secrets management]

## Migration / Backward Compatibility
How does this change affect existing users? Is migration required?
```

**Rule**: Design must specify the "how" with enough detail that a developer could implement it without asking further questions. "Use a cache" is not a design. "Use an in-memory LRU cache with 1000-entry limit and TTL of 5 minutes, evicted on process restart" is.

---

## Phase 4: Implementation Tasks

**File**: `SPEC/tasks.md`

```markdown
# Tasks: <title>

## Task Checklist

### Setup
- [ ] Task 1
- [ ] Task 2

### Core Implementation
- [ ] Task 3
- [ ] Task 4

### Testing
- [ ] Task 5

### Documentation
- [ ] Task 6

## Task Dependencies
- Task 3 requires Task 1 to be complete
- Task 4 can run in parallel with Task 3
```

**Task template:**
```markdown
- [ ] Task: [Description]
  - Acceptance: [What must be true when done]
  - Verify: [How to confirm — test command, build, manual check]
  - Files: [Which files will be touched]
```

**Rule**: Tasks must be small enough to complete in a single session (< 2 hours). If a task is larger, break it down.

---

## Phase 5: Implementation

**Process**:

1. Read `SPEC/tasks.md` — pick the next incomplete task
2. Read the relevant spec section — implement exactly what is specified
3. If TDD skill is available: follow RED-GREEN-REFACTOR cycle
4. Mark each completed task with `✓` in `tasks.md`
5. Write a commit after each completed task

**Code rules**:
- Zero tolerance for TODO comments in code — either do it or file an issue
- No commented-out dead code — delete it
- All new code must pass linting before commit
- Type signatures must be explicit (no `any` without documentation)

**Commit format**:
```
<type>(<scope>): <short description>

[body — what changed and why]
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

---

## Phase 6: Regression Tests

**Before marking any feature complete**, run the full regression test suite.

**Definition**: A regression test is any test that verifies existing, unchanged functionality still works.

```
# Regression test checklist

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
```

**Rule**: If the regression test suite has ANY failures after your change, you cannot proceed to launch until they are fixed or explicitly waived with a documented reason.

---

## Phase 7: Bug-Free Verification

**Before launch**, perform a final verification sweep:

```markdown
# Launch Verification Checklist

## Correctness
- [ ] No `console.error` or unhandled exceptions in code paths
- [ ] All error cases have user-friendly messages (no raw stack traces)
- [ ] Input validation covers all edge cases from the spec
- [ ] No hardcoded secrets, credentials, or API keys

## Testing Coverage
- [ ] New code has unit test coverage ≥ 80% (or documented exception)
- [ ] All acceptance criteria from spec are covered by tests
- [ ] Edge cases from spec are tested

## Performance
- [ ] No obvious N+1 queries (if database is involved)
- [ ] No synchronous operations that could block the event loop (Node.js)

## Security
- [ ] No SQL injection vectors
- [ ] No XSS vectors
- [ ] Auth tokens not logged
- [ ] File paths sanitized

## Rollback
- [ ] Rollback plan from proposal is documented and tested
- [ ] Migrations are reversible (or marked as one-way with justification)
```

---

## Phase 8: Launch

**Pre-launch**:
1. Final verification checklist complete
2. Regression tests green
3. Code review approved (see `requesting-code-review` skill)
4. Changelog updated
5. Version bumped (if applicable)

**Launch execution**:
```bash
# Verify everything is clean
make test && make build && echo "Ready to deploy"

# For infrastructure changes — dry run first
terraform plan -out=plan.tfplan

# Deploy with rollback capability
./scripts/deploy.sh --rollback-on-failure
```

**Post-launch**:
- Monitor error rates for 30 minutes
- Verify success criteria from proposal are being met
- Update proposal with actual outcomes

---

## Keeping the Spec Alive

The spec is a living document, not a one-time artifact:

- **Update when decisions change** — If you discover the data model needs to change, update the spec first, then implement.
- **Update when scope changes** — Features added or cut should be reflected in the spec.
- **Commit the spec** — The spec belongs in version control alongside the code.
- **Reference the spec in PRs** — Link back to the spec section that each PR implements.

---

## Common Rationalizations

These are the ways agents (and humans) rationalize skipping the spec process. Recognize them and push back.

| Rationalization | Reality |
|---|---|
| "This is simple, I don't need a spec" | Simple tasks don't need *long* specs, but they still need acceptance criteria. A two-line spec is fine. |
| "I'll write the spec after I code it" | That's documentation, not specification. The spec's value is in forcing clarity *before* code. |
| "The spec will slow us down" | A 15-minute spec prevents hours of rework. Waterfall in 15 minutes beats debugging in 15 hours. |
| "Requirements will change anyway" | That's why the spec is a living document. An outdated spec is still better than no spec. |
| "The user knows what they want" | Even clear requests have implicit assumptions. The spec surfaces those assumptions. |
| "It's just a small change" | Small changes still break things. The smaller the change, the less excuse to skip the spec. |
| "I'll figure it out as I go" | Without a spec, "figuring it out" means making unilateral decisions that should be reviewed. |

---

## Anti-Patterns (Do NOT Do)

1. **Spec after code** — Writing the spec *after* writing the code defeats the purpose. The spec must exist before code.
2. **Vague acceptance criteria** — "Works correctly" is not acceptance criteria. Be measurable.
3. **Skipping regression tests** — "The change is small, it won't break anything" — it will.
4. **No rollback plan** — Every non-trivial change needs a rollback plan in the proposal.
5. **Implementing outside the spec** — If you found something the spec missed, update the spec first.
6. **Skipping design for "simple" changes** — Most bugs come from "simple" changes that weren't fully thought through.
7. **Silent assumptions** — If you assumed something without writing it down, the spec will mislead implementers.

---

## Red Flags

These are observable signs the spec process is being violated:

- Starting to write code without any written requirements
- Asking "should I just start building?" before clarifying what "done" means
- Implementing features not mentioned in any spec or task list
- Making architectural decisions without documenting them
- Skipping the spec because "it's obvious what to build"
- A spec that has no concrete, testable acceptance criteria
- No "Not Doing" list making trade-offs explicit
- Regression test failures ignored before launch

---

## Quick Reference

| Phase | File | Question Answered | Do Not Proceed If |
|-------|------|-------------------|-------------------|
| Proposal | `SPEC/proposal.md` | Why? What problem? | No problem statement |
| Specs | `SPEC/specs/*.md` | What exactly? | No concrete acceptance criteria |
| Design | `SPEC/design.md` | How? | No implementation detail |
| Tasks | `SPEC/tasks.md` | Who does what? | Tasks > 2 hours each |
| Implement | — | — | Spec not finalized |
| Regression | — | Did we break existing? | Any test failure |
| Verify | — | Is it truly done? | Any checklist item unmet |
| Launch | — | — | Verification incomplete |

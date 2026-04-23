---
name: spec-driven-development
description: >
  Creates specs before coding using a structured artifact pipeline. Use when starting a new
  project, feature, or significant change and no specification exists yet. Use when requirements
  are unclear, ambiguous, or only exist as a vague idea. Inspired by OpenSpec (Fission-AI/OpenSpec,
  42k stars) — the canonical spec-driven development framework.
trigger:
  - "spec"
  - "write a spec"
  - "create a spec"
  - "starting a new project"
  - "开始新项目"
  - "写规格"
  - "规格说明书"
  - "specification"
  - "PRD"
  - "需求文档"
anti_trigger:
  - "single line"  # 单行改动不需要spec
  - "typo"  # typo修正不需要spec
  - "trivial"  # trivial改动不需要spec
  - "already have a spec"  # 已有spec时不需要再写
source: hermes-agent
version: 3.0.0
license: MIT
metadata:
  hermes:
    tags: [Spec, Requirements, SDD, Artifact-Pipeline, OpenSpec]
    related_skills: [source-driven-development, idea-refine, incremental-implementation]
    quality_redlines:
      - MUST have E (Execution) section
      - MUST have B (Boundary) section
      - MUST have A2 (Trigger) section
---

# Spec-Driven Development (SDD)

## Core Principle
**Spec before code** — Write specifications first, then implement. Never start coding without a shared spec.

## Reference: OpenSpec Artifact Pipeline
OpenSpec (github.com/Fission-AI/OpenSpec, 42k stars) defines the canonical artifact pipeline.
Hermes implements the core stages:

```
proposal.md → specs/*.md → design.md → tasks.md → implementation
   (提案)        (详细规格)      (技术设计)     (任务清单)     (执行)
```

- Each artifact depends on its predecessors (tasks.md requires specs AND design)
- Specs are **iterative** — revise as understanding grows
- **Fluid, not rigid** — don't force phase gates; work on what makes sense

## Artifact Formats

### 1. proposal.md — The Why
**Purpose**: Justify the change. Why are we doing this? What problem does it solve?

```markdown
# Proposal: [short title]

## Problem Statement
What pain point or opportunity motivates this?

## Success Criteria
- [ ] Measurable outcome 1
- [ ] Measurable outcome 2

## Out of Scope
What this proposal does NOT cover.

## Alternatives Considered
Why other approaches were rejected.

## Impact
- Breaking changes?
- Migration needed?
- Rollback complexity?
```

### 2. specs/*.md — The What (Requirements + Scenarios)
**Purpose**: Detailed functional requirements with concrete usage scenarios.

```markdown
# Spec: [feature name]

## Functional Requirements
1. **REQ-1**: [requirement statement]
   - Mechanism: HOW this is implemented (not just WHAT)
   - Acceptance: conditions that must be true

2. **REQ-2**: ...

## User Scenarios
### Scenario 1: [title]
**Given** [precondition]
**When** [action]
**Then** [observable result]

### Scenario 2: [title]
...

## Edge Cases
- EC-1: [boundary condition handling]
- EC-2: ...

## Cross-Cutting Concerns
- Error handling strategy
- Logging/observability
- Security considerations
```

### 3. design.md — The How (Technical Design)
**Purpose**: Technical architecture and implementation approach.

```markdown
# Design: [feature name]

## Architecture
[High-level component diagram or description]

## Data Model
[Any new entities, schema changes, API shapes]

## API Surface
[If applicable — endpoints, message types]

## Key Design Decisions
1. **Decision**: [description]
   - **Rationale**: why this approach
   - **Alternatives**: what was considered and rejected

## Platform Considerations
- macOS / Linux / Windows handling
- Any environment-specific behavior

## Security & Performance
[If non-trivial]
```

### 4. tasks.md — The Checklist (Source of Truth for Implementation)
**Purpose**: Granular checklist that drives implementation. AI reads this and marks items complete.

```markdown
# Tasks: [feature name]

## Task Checklist
- [ ] TASK-1: [specific actionable item]
- [ ] TASK-2: [specific actionable item]
- [ ] TASK-3.1: [subtask of TASK-3]
- [ ] TASK-3.2: [subtask of TASK-3]

## Verification
- [ ] All tasks complete
- [ ] Tests pass
- [ ] Docs updated
- [ ] No regression
```

**Critical rule**: Tasks must be **specific and checkable** — not vague goals. Each task should be verifiable as done or not done.

## SDD Workflow in Hermes

1. **Assess** — Is there already a spec? Is this change large enough to need one?
2. **Detect triggers** — If any anti-trigger fires, skip spec creation
3. **Create artifacts** — Write proposal, specs, design, tasks in that order
4. **Implement** — Read tasks.md and check off items as you go
5. **Verify** — Ensure all tasks complete, all scenarios covered
6. **Update spec** — If implementation reveals spec gaps, revise artifacts

## Quality Gates (all MUST pass before implementation)

| Gate | Check |
|------|-------|
| **E (Execution)** | Can you actually implement this? Resources/time/tools available? |
| **B (Boundary)** | Are limits and edge cases defined? |
| **A2 (Trigger)** | Is the activation condition specific enough? |
| **Scenarios** | Do scenarios cover happy path AND failure modes? |
| **Tasks** | Is every REQ linked to at least one task? |

## OpenSpec-Inspired Principles

- **Fluid over rigid**: Don't force waterfall stages. Propose → iterate → implement when ready
- **Brownfield-first**: Always consider existing code, don't design in a greenfield vacuum
- **Cross-platform**: Path handling, line endings, env-specific behavior must be in specs
- **Mechanisms over features**: "HOW it works" matters as much as "WHAT it does"

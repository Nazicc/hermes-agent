---
name: writing-plans
description: >
  Creates comprehensive implementation plans with bite-sized tasks, exact file paths,
  and complete code examples. Use when you have a spec or requirements for a multi-step task.
trigger:
  - "write a plan"
  - "create a plan"
  - "implementation plan"
  - "how do I implement"
  - "做计划"
  - "实施计划"
  - "implementation"
  - "开发计划"
  - "task breakdown"
anti_trigger:
  - "single step"  # 一步就完成不需要做计划
  - "already have a plan"  # 已有计划不需要再写
  - "我知道怎么做"  # 用户已知道怎么做
source: hermes-agent (adapted from obra/superpowers)
version: 2.0.0
license: MIT
metadata:
  sources: []
  hermes:
    quality_redlines:
      - MUST have E (Execution) section
      - MUST have B (Boundary) section
      - MUST have A2 (Trigger) section
    tags: [planning, design, implementation, workflow, documentation]
    related_skills: [subagent-driven-development, test-driven-development, requesting-code-review]
---
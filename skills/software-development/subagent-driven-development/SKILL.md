---
name: subagent-driven-development
description: >
  Executes implementation plans via fresh delegate_task per task with two-stage review:
  spec compliance first, then code quality.
  Use when executing multi-task plans from writing-plans skill.
trigger:
  - "run the plan"
  - "execute the plan"
  - "implement the plan"
  - "start implementing"
  - "开始执行"
  - "开始实现"
  - "run subagent"
  - "dispatch subagent"
anti_trigger:
  - "single file"  # 单文件改动不需要subagent编排
  - "one task only"  # 只有一个任务不需要subagent驱动
  - "不需要并行"
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
    tags: [delegation, subagent, implementation, workflow, parallel]
    related_skills: [writing-plans, requesting-code-review, test-driven-development]
---
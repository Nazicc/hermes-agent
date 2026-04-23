---
name: incremental-implementation
description: >
  Delivers changes incrementally — thin vertical slices, test each, verify each, commit each.
  Use when implementing any feature or change that touches more than one file.
  Use when you're about to write a large amount of code at once, or when a task feels too big to land in one step.
trigger:
  - "implement"
  - "开始实现"
  - "开始写代码"
  - "写代码"
  - "implement feature"
  - "实现功能"
  - "how do I build"
  - "怎么实现"
  - "refactor"
  - "重构"
anti_trigger:
  - "single line"  # 单行改动不需要增量
  - "one function"  # 单函数改动不需要增量
  - "trivial"  # trivial 改动不需要增量
  - "只改一行"
source: hermes-agent
version: 2.0.0
license: MIT
metadata:
  sources: []
  hermes:
    quality_redlines:
      - MUST have E (Execution) section
      - MUST have B (Boundary) section
      - MUST have A2 (Trigger) section
---
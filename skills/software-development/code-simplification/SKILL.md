---
name: code-simplification
description: >
  Simplifies code for clarity without changing behavior.
  Use when code works but is harder to read, maintain, or extend than it should be.
  Use when refactoring code for clarity.
  Use when encountering deeply nested logic, long functions, or unclear names.
trigger:
  - "simplify"
  - "simplify this code"
  - "重构"
  - "clean up"
  - "代码太复杂"
  - "代码简化"
  - " readability"
  - "可读性"
  - "太乱了"
anti_trigger:
  - "it works fine, leave it alone"  # 代码本来就清晰，不需要简化
  - "performance critical"  # 性能关键路径，不是简化场景
  - "I don't understand what this code does yet"  # 不理解代码时不要简化
  - "rewrite from scratch"  # 全新重写不是简化
  - "我不懂这段代码"
source: hermes-agent (inspired by anthropics/claude-code plugins/code-simplifier)
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
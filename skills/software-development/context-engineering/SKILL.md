---
name: context-engineering
description: >
  Optimizes agent context setup. Use when starting a new session, when agent output quality degrades,
  when switching between tasks, or when you need to configure rules files and context for a project.
trigger:
  - "context"
  - "setup context"
  - "new session"
  - "quality is degrading"
  - "上下文"
  - "会话开始"
  - "start a new session"
  - "agent quality"
  - "上下文设置"
anti_trigger:
  - "I already told you everything"  # 用户已提供所有上下文
  - "just do it"  # 不需要上下文工程，直接执行
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
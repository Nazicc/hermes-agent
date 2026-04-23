---
name: idea-refine
description: >
  Refines raw ideas into sharp, actionable concepts worth building.
  Use when user has a vague idea and needs structured divergent and convergent thinking.
trigger:
  - "ideate"
  - "refine this idea"
  - "help me think through"
  - "brainstorm"
  - "创意"
  - "头脑风暴"
  - "想法"
  - "idea"
anti_trigger:
  - "already have a clear plan"  # 已有清晰计划不需要再ideate
  - "just implement it"  # 不需要再想，直接实现
  - "我知道要做什么"  # 用户已知道做什么
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
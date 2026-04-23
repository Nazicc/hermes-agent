---
name: spec-driven-development
description: >
  Creates specs before coding. Use when starting a new project, feature, or significant change
  and no specification exists yet. Use when requirements are unclear, ambiguous, or only exist as a vague idea.
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
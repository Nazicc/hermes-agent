---
name: hermes-evolver-integration
description: >
  Integrate Hermes Agent with Evolver (EvoMap/evolver) via lightweight bridge —
  sync Hermes session logs to Evolver's scan directory, then trigger evolution analysis.
  Use when you want evolver to process Hermes sessions and generate evolution suggestions.
trigger:
  - "evolver"
  - "evolution"
  - "gep"
  - "self-evolution"
  - "进化"
  - "gene"
  - "信号"
  - "process sessions with evolver"
  - "触发evolution"
anti_trigger:
  - "不需要evolver"  # 不需要集成evolver
  - "don't need evolution"  # 不需要evolution功能
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
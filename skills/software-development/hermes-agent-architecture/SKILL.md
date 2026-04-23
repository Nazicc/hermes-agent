---
name: hermes-agent-architecture
description: >
  Hermes Agent 项目架构 — cli.py、run_agent.py、HermesCLI、AIAgent 的关系，
  以及如何正确添加新命令和 handlers。
  Use when modifying Hermes codebase, adding new commands, or understanding Hermes internals.
trigger:
  - "modify hermes"
  - "add command to hermes"
  - "change cli.py"
  - "add handler"
  - "Hermes源码"
  - "Hermes架构"
  - "修改Hermes"
  - "添加命令"
  - "hermes-agent codebase"
  - "Hermes内部"
anti_trigger:
  - "使用Hermes"  # 只是使用Hermes不需要了解架构
  - "just use hermes"  # 只是使用不是修改
  - "配置Hermes"  # 配置不等于修改代码
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
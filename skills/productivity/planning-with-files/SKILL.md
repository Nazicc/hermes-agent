---
name: planning-with-files
description: Manus-style file-based planning wrapper. Creates task_plan.md, findings.md, progress.md to track complex multi-step tasks across sessions. Use when user asks to "plan", "organize", "break down" a project, or when a task requires 5+ tool calls.
user-invocable: true
version: 2.0.0
license: MIT
metadata:
  sources: []
  hermes:
    quality_redlines:
      - MUST have E (Execution) section
      - MUST have B (Boundary) section
      - MUST have A2 (Trigger) section
      - Wrapper skill — references upstream planning-with-files repo
      - Does NOT implement hook system (observe-only for now)
---
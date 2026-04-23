---
name: requesting-code-review
description: >
  Pre-commit verification pipeline — static security scan, baseline-aware
  quality gates, independent reviewer subagent, and auto-fix loop.
  Use when user says "commit", "push", "ship", "verify", or "review before merge".
  Use after code changes and before committing, pushing, or opening a PR.
trigger:
  - "commit"
  - "push"
  - "ship"
  - "verify"
  - "review before merge"
  - "需要提交"
  - "审核"
  - "代码审查"
  - "帮我看看代码"
  - "review"
anti_trigger:
  - "帮我review别人的PR"  # → github-code-review skill
  - "review a PR on GitHub"
  - "帮我审核他人的PR"
source: hermes-agent (adapted from obra/superpowers + MorAlekss)
version: 2.0.0
license: MIT
metadata:
  sources: []
  hermes:
    quality_redlines:
      - MUST have E (Execution) section
      - MUST have B (Boundary) section
      - MUST have A2 (Trigger) section
    tags: [code-review, security, verification, quality, pre-commit, auto-fix]
    related_skills: [subagent-driven-development, writing-plans, test-driven-development, github-code-review]
---
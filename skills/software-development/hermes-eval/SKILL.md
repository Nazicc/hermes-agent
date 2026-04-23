---
name: hermes-eval
description: |
  Hermes Agent Skill Evaluation Harness — 自动化评测 skills 质量的框架。
  每个 skill 有独立 YAML suite，包含多维度测试用例（reasoning/command/file_edit）。
  接入 weekly cron 后，所有 skill 升级必须先 PASS harness，否则跳过升级。
  Trigger: 用户说"跑一下评测"、eval"、"测试skill"、或每周 cron 自动触发。
  Anti-trigger: 纯信息查询。
trigger:
  - "评测"
  - "eval"
  - "测试skill"
  - "跑一下测试"
  - "hermes-eval"
  - "质量"
anti_trigger:
  - "只是问问"
  - "怎么写"
version: 2.0.0
license: MIT
metadata:
  sources: []
  hermes:
    tags: [evaluation, testing, quality, benchmark, skill-assessment]
    related_skills: [skills-evolution-from-research, systematic-debugging, test-driven-development]
    quality_redlines:
      - MUST have R (Reference) section with RIA-TV++ format description
      - MUST have E (Execution) section with harness.py usage
      - MUST have A2 (Trigger) section with activation signals
      - MUST have B (Boundary) section with anti-triggers
      - harness.py MUST be runnable without API key (degrades gracefully)
---
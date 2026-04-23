---
name: source-driven-development
description: >
  Grounds every implementation decision in official documentation.
  Use when building with any framework or library where correctness matters.
  Use when you want authoritative, source-cited code free from outdated patterns.
trigger:
  - "use"
  - "official docs"
  - "check the documentation"
  - "what does the docs say"
  - "how do I use"
  - "official documentation"
  - "框架"
  - "官方文档"
  - "文档说"
  - "怎么用"
anti_trigger:
  - "pure logic"  # 纯逻辑不依赖框架
  - "simple renaming"  # 简单重命名不依赖文档
  - "I know this API by heart"  # 跳过文档验证
  - "just quickly"
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
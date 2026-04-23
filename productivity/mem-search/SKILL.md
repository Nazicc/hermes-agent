---
name: mem-search
description: >
  'Three-layer memory search protocol for SimpleMem/MemPalace. Step 1: search index → Step 2: timeline context → Step 3: fetch full entries. Inspired by claude-mem''s mem-search skill (65k stars). Saves 10x tokens by filtering before fetching full details. Triggers:

  '
triggers:
- search memory
- query memories
- find in past sessions
- did we already solve this
- how did we do X last time
- search SimpleMem
- memory search


# Memory Search — Three-Layer Protocol

> 引用自 claude-mem `mem-search` skill 设计。节省 10x tokens。

## 适用场景

用户问及**历史会话**（非当前对话）：
- "上次这个 bug 是怎么修的？"
- "之前我们做过这个功能吗？"
- "上周发生了什么？"

## 三层工作流

**核心原则：永远先过滤，再取详情。**
license: MIT
metadata:
  hermes:
    tags: []
    related_skills: []
---
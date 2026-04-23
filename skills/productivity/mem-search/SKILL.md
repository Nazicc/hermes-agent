---
name: mem-search
description: 'Three-layer memory search protocol for SimpleMem/MemPalace. Step 1:
  search index → Step 2: timeline context → Step 3: fetch full entries. Inspired by
  claude-mem''s mem-search skill (65k stars). Saves 10x tokens by filtering before
  fetching full details.

  '
triggers:
- search memory
- query memories
- find in past sessions
- did we already solve this
- how did we do X last time
- search SimpleMem
- memory search
license: MIT
metadata:
  hermes:
    tags: []
    related_skills: []
---
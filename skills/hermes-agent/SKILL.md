---
name: hermes-agent
description: Complete guide to using and extending Hermes Agent — CLI usage, setup, configuration, spawning additional agents, gateway platforms, skills, voice, tools, profiles, and a concise contributor reference. Load this skill when helping users configure Hermes, troubleshoot issues, spawn agent instances, or make code contributions.
version: 2.0.0
author: Hermes Agent + Teknium
license: MIT
metadata:
  sources: []
  hermes:
    tags: [hermes, setup, configuration, multi-agent, spawning, cli, gateway, development]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [claude-code, codex, opencode]
---

## Critical Operational Facts (2026-04-24)

**Always use these paths — incorrect assumptions cause silent failures:**

### Skills System Paths

| What | Correct Path |
|------|-------------|
| Skills directory | `~/.hermes/skills/skills/{name}/SKILL.md` |
| Snapshot cache | `~/.hermes/.skills_prompt_snapshot.json` |
| Hermes home | `~/.hermes/` |

**Common mistake**: `~/.hermes/hermes-agent/skills/` is WRONG for the skills system. The skills system reads from `~/.hermes/skills/skills/`, NOT from the hermes-agent git repo's skills subdirectory.

### Snapshot Cache

After installing or modifying skills, DELETE `~/.hermes/.skills_prompt_snapshot.json` to force a rebuild of the skills index. Otherwise newly installed skills won't appear.

### execute_code Write Operations Are Sandboxed

`execute_code` write_file/terminal operations run in an isolated VM — they do NOT persist to the real filesystem. Always use `terminal()` with raw Python for file I/O that must survive the session:

```python
# ✅ CORRECT — persists to real filesystem
python3 -c "
with open('/path/to/file', 'w') as f:
    f.write(content)
"

# ❌ WRONG — written to execute_code VM, lost immediately
write_file('/path/to/file', content)
```

### Git Clone Structure

There are two clones of the hermes-agent repo:
- `~/.hermes/skills/` — with capital `N` (Nazicc), this is what the skills system reads
- `~/.hermes/hermes-agent/` — with lowercase `n` (nazicc), alternate clone

Both push to `git@github.com:Nazicc/hermes-agent.git`. Use `~/.hermes/skills/` as the canonical working directory for skills work.
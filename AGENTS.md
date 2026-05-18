# Hermes Agent - Development Guide

Instructions for AI coding assistants working on the hermes-agent codebase.

## ⚖️ Constitution

**This project is governed by a constitution.** The canonical file is `.hermes/memory/constitution.md`.
It defines 7 non-negotiable principles: Session Completeness, Test-First, Memory Hygiene,
Skill Reuse, Analysis-Before-Action, Simplicity (YAGNI), Observability.

Load `constitution-enforcer` at session start. Gate checks are mandatory — violations of
principles I, II, or V are blocking. III, IV, VI, VII are advisory.

## Development Environment

```bash
source .venv/bin/activate   # or: source venv/bin/activate
```

`scripts/run_tests.sh` probes `.venv` first, then `venv`, then `$HOME/.hermes/hermes-agent/venv`.

## Project Structure

```
hermes-agent/
├── run_agent.py          # AIAgent class — core conversation loop
├── model_tools.py        # Tool orchestration, discover_builtin_tools()
├── toolsets.py           # Toolset definitions, _HERMES_CORE_TOOLS list
├── cli.py                # HermesCLI class — interactive CLI
├── hermes_state.py       # SessionDB — SQLite session store (FTS5 search)
├── hermes_constants.py   # get_hermes_home(), display_hermes_home() — profile-aware paths
├── agent/                # Agent internals (providers, memory, caching, compression)
├── hermes_cli/           # CLI subcommands, setup wizard, plugins loader, skin engine
├── tools/                # Tool implementations — auto-discovered via tools/registry.py
│   └── environments/     # Terminal backends (local, docker, ssh, modal, ...)
├── gateway/              # Messaging gateway — run.py + platforms/
├── plugins/              # Plugin system (memory providers, model providers, kanban, ...)
├── skills/               # Built-in skills bundled with the repo
├── optional-skills/      # Heavier/niche skills — installed explicitly via `hermes skills install`
├── ui-tui/               # Ink (React) terminal UI — `hermes --tui`
├── tui_gateway/          # Python JSON-RPC backend for the TUI
├── acp_adapter/          # ACP server (VS Code / Zed / JetBrains integration)
├── cron/                 # Scheduler — jobs.py, scheduler.py
├── scripts/              # run_tests.sh, release.py
└── tests/                # Pytest suite
```

**User config:** `~/.hermes/config.yaml` (settings), `~/.hermes/.env` (API keys only).
**Logs:** `~/.hermes/logs/` — `agent.log` (INFO+), `errors.log` (WARNING+), `gateway.log`.
Profile-aware via `get_hermes_home()`.

### File Dependency Chain

```
tools/registry.py → tools/*.py → model_tools.py → run_agent.py, cli.py
```

---

## AIAgent (run_agent.py)

The core loop inside `run_conversation()`:

```python
while (api_call_count < max_iterations and iteration_budget.remaining > 0) or _budget_grace_call:
    response = client.chat.completions.create(model=model, messages=messages, tools=tool_schemas)
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = handle_function_call(tool_call.name, tool_call.args, task_id)
            messages.append(tool_result_message(result))
    else:
        return response.content
```

Messages follow OpenAI format. Reasoning content stored in `assistant_msg["reasoning"]`.

## CLI Architecture (cli.py)

- **Rich** for banner/panels, **prompt_toolkit** for input with autocomplete
- `process_command()` dispatches on canonical command name from central registry
- Skill slash commands (`agent/skill_commands.py`) scan `~/.hermes/skills/`; inject as **user message** (not system prompt) to preserve prompt caching

### Slash Command Registry (`hermes_cli/commands.py`)

All slash commands in `COMMAND_REGISTRY` list of `CommandDef` objects. Every consumer derives automatically:
CLI, Gateway, Gateway help, Telegram bot commands, Slack subcommands, autocomplete, CLI help.

To add a command: add `CommandDef` to `COMMAND_REGISTRY`, handler in `HermesCLI.process_command()`,
and (if gateway-available) handler in `gateway/run.py`. Aliases only need adding to the `aliases` tuple.

---

## Adding New Tools

For custom/local tools, use the plugin route (`~/.hermes/plugins/<name>/` + `ctx.register_tool()`).
For core tools: create `tools/your_tool.py` with `registry.register()` call, then add name to
a toolset in `toolsets.py` (auto-discovery imports the file, but manual wiring into a toolset
is required for the tool to be exposed). All handlers MUST return a JSON string.

Use `get_hermes_home()` for state file paths, never `Path.home() / ".hermes"`.

---

## Plugins

Two surfaces under `plugins/`:

1. **General** (`hermes_cli/plugins.py`): discovers from `~/.hermes/plugins/`, `.hermes/plugins/`, pip entry points.
   `register(ctx)` can add hooks, tools, CLI subcommands. **Rule: plugins MUST NOT modify core files.**

2. **Model providers** (`plugins/model-providers/`): each calls `providers.register_provider(ProviderProfile(...))`.
   Lazy discovery via `providers/__init__.py._discover_providers()`. User plugins override bundled ones.

Scan order: bundled → user `$HERMES_HOME/plugins/` → legacy `<repo>/providers/<name>.py`.

---

## Skills

Two surfaces:
- `skills/` — built-in, loadable by default
- `optional-skills/` — heavier/niche, installed via `hermes skills install official/<category>/<skill>`

### SKILL.md frontmatter

Standard fields: `name`, `description`, `version`, `author`, `license`, `platforms`,
`metadata.hermes.tags`, `metadata.hermes.category`, `metadata.hermes.related_skills`,
`metadata.hermes.config`.

### Skill Authoring Standards (HARDLINE)

1. **`description` ≤ 60 characters**, one sentence, ends with period. No marketing words.
2. **Tools referenced must be native Hermes tools** (`` `terminal` ``, `` `search_files` `` etc.) or MCP servers the skill expects. Don't name raw shell utilities (`grep` → `search_files`, `sed` → `patch`).
3. **`platforms:` gating audited against actual script imports.** POSIX-only primitives → gate to linux/macos.
4. **`author` credits the human contributor first.** Replace "Hermes Agent" author with actual name for external contributions.
5. **Modern section order:** title, intro, `## When to Use`, `## Prerequisites`, `## How to Run`, `## Quick Reference`, `## Procedure`, `## Pitfalls`, `## Verification`.
6. **Scripts go in `scripts/`, references in `references/`, templates in `templates/`.**
7. **Tests at `tests/skills/test_<skill>_skill.py`**, stdlib + pytest + mock only.
8. **`.env.example` additions isolated to delimited block.**

---

## Toolsets

Defined in `toolsets.py` as `TOOLSETS` dict. Key sets: `browser`, `code_execution`, `cronjob`,
`delegation`, `file`, `search`, `session_search`, `skills`, `terminal`, `todo`, `vision`, `web`, etc.

Enable/disable per platform via `hermes tools` or `config.yaml` lists.

---

## Delegation (`delegate_task`)

`tools/delegate_tool.py` spawns isolated subagents. Two shapes: single (`goal`) or batch (`tasks: [...]`).
Roles: `leaf` (no further delegation), `orchestrator` (can spawn workers, gated by `delegation.orchestrator_enabled`,
bounded by `delegation.max_spawn_depth`). Synchronous — not durable. Use `cronjob` or
`terminal(background=True, notify_on_complete=true)` for work that must outlive the current turn.

---

## Cron (scheduled jobs)

`cron/jobs.py` + `cron/scheduler.py`. Jobs scheduled via `cronjob` tool or `hermes cron <verb>`.
Schedule formats: duration (`"30m"`), "every" phrases, 5-field cron, ISO timestamps.
Hardening: 3-min interrupt on cron sessions, file lock prevents duplicate ticks, memory providers
skip during cron runs.

---

## Important Policies

### Prompt Caching Must Not Break

Do NOT implement changes that would alter past context, change toolsets, reload memories,
or rebuild system prompts mid-conversation. Cache-breaking forces dramatically higher costs.
The ONLY time we alter context is during context compression.

Slash commands that mutate system-prompt state must be cache-aware: defer to next session
by default, opt-in `--now` flag for immediate invalidation.

### DO NOT hardcode `~/.hermes` paths

Use `get_hermes_home()` for code paths, `display_hermes_home()` for user-facing messages.
Hardcoding breaks profiles.

---

## Profiles: Multi-Instance Support

Each profile has its own `HERMES_HOME` directory. `_apply_profile_override()` sets `HERMES_HOME`
before any module imports. All `get_hermes_home()` references auto-scope.

Key rules:
- Use `get_hermes_home()` for paths, `display_hermes_home()` for display
- Module-level constants are fine (cached after profile override)
- Gateway platform adapters should use `acquire_scoped_lock()` to prevent two profiles sharing credentials
- Profile operations are HOME-anchored (`Path.home() / ".hermes" / "profiles"`), not HERMES_HOME-anchored

---

## Key Pitfalls

- **Hardcoded `~/.hermes` paths** — use `get_hermes_home()`. Source of 5 bugs fixed in PR #3575.
- **`_last_resolved_tool_names`** is process-global in `model_tools.py`. `_run_single_child()` saves/restores it around subagents.
- **No cross-tool references in tool schemas** — tools from other toolsets may be unavailable.
  Add dynamic cross-references in `get_tool_definitions()` in `model_tools.py`.
- **Gateway has TWO message guards** — new commands must bypass both to reach the runner during active agent.
- **Squash merges from stale branches** silently revert recent fixes. Ensure branch is up to date with `main` before squash.
- **Tests must not write to `~/.hermes/`** — `_isolate_hermes_home` autouse fixture redirects `HERMES_HOME` to temp dir.
  Profile tests must also mock `Path.home()`.

---

## Testing

**ALWAYS use `scripts/run_tests.sh`** — not `pytest` directly. The script enforces CI-parity:
unsets all `*_API_KEY`/`*_TOKEN` vars, sets `TZ=UTC` + `LANG=C.UTF-8`, uses `-n 4` xdist workers.
Direct `pytest` on a developer machine with API keys set diverges from CI.

```bash
scripts/run_tests.sh                                  # full suite
scripts/run_tests.sh tests/gateway/                   # one directory
scripts/run_tests.sh tests/agent/test_foo.py::test_x  # one test
```

### Don't Write Change-Detector Tests

Tests that fail when data expected to change gets updated (model catalogs, config version numbers,
enumeration counts, hardcoded provider model lists) add no behavioral coverage. They guarantee
routine source updates break CI.

**Do write** invariants (e.g., "every model in the catalog has a context-length entry"),
not snapshots of current data ("catalog contains exactly model X").

Always run the full suite before pushing.

<p align="center">
  <img src="assets/banner.png" alt="Hermes Agent" width="100%">
</p>

# Hermes Agent ☤

<p align="center">
  <a href="https://hermes-agent.nousresearch.com/docs/"><img src="https://img.shields.io/badge/Docs-hermes--agent.nousresearch.com-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/NousResearch/hermes-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://nousresearch.com"><img src="https://img.shields.io/badge/Built%20by-Nous%20Research-blueviolet?style=for-the-badge" alt="Built by Nous Research"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
</p>

**The self-improving AI agent built by [Nous Research](https://nousresearch.com).** It's the only agent with a built-in learning loop — it creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions. Run it on a $5 VPS, a GPU cluster, or serverless infrastructure that costs nearly nothing when idle.

## Architecture

<p align="center">
  <a href="docs/diagrams/hermes-architecture.html"><b>📐 Open Architecture Diagram →</b></a><br>
  <em>(dark-themed SVG — open in browser)</em>
</p>

Hermes Agent is built in layers:

- **Gateway** — 18 messaging platforms (Feishu, Telegram, Discord, Slack, WhatsApp, Signal, WeChat, WeCom, Matrix, SMS, Email, DingTalk, Mattermost, Home Assistant, BlueBubbles, Yuanbao, Webhooks) + REST/WebSocket API. All feed into a single agent loop with cross-platform session continuity.
- **Core Agent Loop** — `run_agent.py` orchestrates `agent/` modules: **Prompt Builder** (skills injection, Progressive Disclosure of AGENTS.md/CLAUDE.md → pointer mode), **Context Engine** (compression, token budgeting, trajectory management), **Tool Execution** (40+ tools across 10 toolsets), **Model/Provider** routing (multi-provider with credential pool and fallback chains).
- **Memory System (L0–L3)** — 4-layer progressive memory unified via `memory_recall`:
  - **L0** — Injected context: MEMORY.md + USER.md + AGENTS.md pointer (~2,200 chars) in system prompt
  - **L1** — Working memory: per-session state, tool results, context compression
  - **L2** — OpenViking Knowledge Base: semantic search, structured URI space (viking://)
  - **Hindsight** — Graph reasoning: pattern detection, reflection, mental models
  - **L3** — Evolution signals: skill auto-creation, quality scoring, nudge system
- **Skills System** — 32+ categories of reusable procedural knowledge in `~/.hermes/skills/`. Self-evolving: agents auto-create skills after complex tasks and improve them during use. Compatible with [agentskills.io](https://agentskills.io).
- **Delegation** — Subagent spawning with isolated contexts, parallel workstreams, ACP transports (Claude Code, Codex, Codebuff, OpenCode).
- **Cron Scheduler** — Natural-language scheduled tasks with platform delivery, watchdog scripts, chain jobs.
- **MCP Integration** — Native MCP client + mcporter bridge. Built-in servers: browser-harness, deepcode, deeptutor, deerflow, sirchmunk, beads, hindsight, skills-quality.
- **Self-Evolution** — Agent-curated learning loop: auto-creates skills after complex tasks, patches them during use, quality scoring (stub→developing→good→excellent), curator runs daily LLM reviews. CMA-inspired: ToolResult standardization (`agent/tool_result.py`) and Session Event Log (`agent/session_event_log.py`) for traceability.

See the full [memory flow diagram](docs/diagrams/hermes-memory-flow.html) for how data flows through the L0–L3 layers.

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

After installation:

```bash
source ~/.bashrc    # reload shell (or: source ~/.zshrc)
hermes              # start chatting!
```

## Getting Started

```bash
hermes              # Interactive CLI — start a conversation
hermes model        # Choose your LLM provider and model
hermes tools        # Configure which tools are enabled
hermes config set   # Set individual config values
hermes gateway      # Start the messaging gateway
hermes setup        # Run the full setup wizard
hermes update       # Update to the latest version
hermes doctor       # Diagnose any issues
```

📖 **[Full documentation →](https://hermes-agent.nousresearch.com/docs/)**

## Key Features

<table>
<tr><td><b>Multi-Platform</b></td><td>18 messaging platforms + CLI/TUI + REST API. Cross-platform session continuity, voice transcription, media delivery.</td></tr>
<tr><td><b>Closed Learning Loop</b></td><td>Agent-curated 4-layer memory (L0–L3), automatic skill creation, skill self-improvement, session search with FTS5 + LLM summarization, Hindsight graph reasoning.</td></tr>
<tr><td><b>Progressive Disclosure</b></td><td>AGENTS.md, CLAUDE.md, .cursorrules injected as pointers (~930 chars) instead of full content. Agent loads on-demand via read_file, saving ~93% context overhead.</td></tr>
<tr><td><b>Delegation & Parallelism</b></td><td>Spawn isolated subagents for parallel workstreams. Python code execution with RPC tools for zero-context-cost multi-step pipelines.</td></tr>
<tr><td><b>Scheduled Automation</b></td><td>Built-in cron scheduler with platform delivery. Daily reports, nightly backups, weekly audits — all in natural language.</td></tr>
<tr><td><b>Run Anywhere</b></td><td>Seven terminal backends: local, Docker, SSH, Singularity, Modal, Daytona, Vercel Sandbox. Serverless hibernation on idle.</td></tr>
<tr><td><b>Any Model</b></td><td>DeepSeek, GLM, OpenAI, Anthropic, OpenRouter (200+), NVIDIA NIM, Hugging Face, Kimi, z.ai, custom providers — switch with <code>hermes model</code>.</td></tr>
<tr><td><b>MCP Ecosystem</b></td><td>Native MCP client + mcporter bridge. Connect 8+ built-in MCP servers for browsers, code analysis, research, search, issue tracking, and more.</td></tr>
<tr><td><b>Research-Ready</b></td><td>Batch trajectory generation, Atropos RL environments, trajectory compression for training next-gen tool-calling models.</td></tr>
</table>

## CLI vs Messaging Quick Reference

| Action | CLI | Messaging platforms |
|---------|-----|---------------------|
| Start chatting | `hermes` | Run `hermes gateway setup` + `hermes gateway start`, then send the bot a message |
| Start fresh conversation | `/new` or `/reset` | `/new` or `/reset` |
| Change model | `/model [provider:model]` | `/model [provider:model]` |
| Set a personality | `/personality [name]` | `/personality [name]` |
| Retry or undo the last turn | `/retry`, `/undo` | `/retry`, `/undo` |
| Compress context / check usage | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]` |
| Browse skills | `/skills` or `/<skill-name>` | `/<skill-name>` |
| Interrupt current work | `Ctrl+C` or send a new message | `/stop` or send a new message |
| Platform-specific status | `/platforms` | `/status`, `/sethome` |

For the full command lists, see the [CLI guide](https://hermes-agent.nousresearch.com/docs/user-guide/cli) and the [Messaging Gateway guide](https://hermes-agent.nousresearch.com/docs/user-guide/messaging).

## Documentation

All documentation lives at **[hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/)**:

| Section | What's Covered |
|---------|---------------|
| [Quickstart](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart) | Install → setup → first conversation in 2 minutes |
| [CLI Usage](https://hermes-agent.nousresearch.com/docs/user-guide/cli) | Commands, keybindings, personalities, sessions |
| [Configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) | Config file, providers, models, all options |
| [Messaging Gateway](https://hermes-agent.nousresearch.com/docs/user-guide/messaging) | 18 platforms, cross-platform continuity |
| [Security](https://hermes-agent.nousresearch.com/docs/user-guide/security) | Command approval, DM pairing, container isolation |
| [Tools & Toolsets](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools) | 40+ tools, toolset system, terminal backends |
| [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) | Procedural memory, Skills Hub, creating skills |
| [Memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) | L0-L3 layered memory, user profiles, best practices |
| [MCP Integration](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) | Connect any MCP server for extended capabilities |
| [Cron Scheduling](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) | Scheduled tasks with platform delivery |
| [Context Files](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files) | Progressive Disclosure for AGENTS.md/CLAUDE.md |
| [Architecture](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture) | Project structure, agent loop, key classes |
| [Contributing](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing) | Development setup, PR process, code style |
| [CLI Reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) | All commands and flags |
| [Environment Variables](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) | Complete env var reference |

## Memory System

Hermes Agent uses a 4-layer progressive memory system, unified by the `memory_recall` tool:

| Layer | Name | Persistence | Storage | Purpose |
|-------|------|-------------|---------|---------|
| **L0** | Injected Context | Per-session | System prompt | Durable facts, user profile, AGENTS.md pointer — always in context |
| **L1** | Working Memory | Per-session | `hermes_memory_data/` | Conversation history, tool results, context compression |
| **L2** | OpenViking KB | Permanent | Semantic store (viking://) | Long-term knowledge, entity/event/pattern/preference storage |
| **Hindsight** | Graph Reasoning | Permanent | PostgreSQL/pgvector | Pattern detection, reflection, mental models, multi-strategy retrieval |
| **L3** | Evolution Signals | Permanent | Skills system | Skill auto-creation, quality scoring, nudge-driven improvement |

Memory is written via dual-path L0→L2 sync (memory tool writes to both immediately), with Hindsight for graph-level analysis and L3 for self-improvement. Query via `memory_recall` for unified multi-layer retrieval or individual tools (`viking_search`, `hindsight_recall`, `session_search`) for targeted access.

<p align="center">
  <a href="docs/diagrams/hermes-memory-flow.html"><b>📐 Open Memory Flow Diagram →</b></a><br>
  <br><em>Memory Flow Architecture — L0 through L3, unified by memory_recall()</em>
</p>

## Progressive Disclosure

Hermes Agent uses **Progressive Disclosure** for context files: AGENTS.md, CLAUDE.md, and .cursorrules are injected as lightweight pointers (~930 chars combined) instead of their full text. The agent loads content on-demand via `read_file()`, saving ~93% context overhead while maintaining full access.

The HERMES.md / SOUL.md file is loaded in full (it's user-authored, typically short, and highest priority).

This is implemented in `agent/prompt_builder.py` via `_context_file_pointer_md()` and the three context-file loading functions.

## Contributing

We welcome contributions! See the [Contributing Guide](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing) for development setup, code style, and PR process.

Quick start for contributors — clone and go:

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
./setup-hermes.sh     # installs uv, creates venv, installs .[all], symlinks ~/.local/bin/hermes
./hermes              # auto-detects the venv, no need to `source` first
```

Manual path (equivalent to the above):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv .venv --python 3.11
source .venv/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

> **RL Training (optional):** The RL/Atropos integration (`environments/`) — see [`CONTRIBUTING.md`](https://github.com/NousResearch/hermes-agent/blob/main/CONTRIBUTING.md#development-setup) for the full setup.

## Community

- 💬 [Discord](https://discord.gg/NousResearch)
- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Issues](https://github.com/NousResearch/hermes-agent/issues)
- 🔌 [HermesClaw](https://github.com/AaronWong1999/hermesclaw) — Community WeChat bridge

## License

MIT — see [LICENSE](LICENSE).

Built by [Nous Research](https://nousresearch.com).
# Hermes Agent ☤

<p align="center">
  <img src="assets/banner.png" alt="Hermes Agent" width="100%">
</p>
<p align="center">
  <a href="https://github.com/Nazicc/hermes-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://github.com/Nazicc/hermes-agent"><img src="https://img.shields.io/badge/Stars-19.3k-orange?style=for-the-badge" alt="Stars"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
</p>

**A fork of <a href="https://github.com/NousResearch/hermes-agent">NousResearch/hermes-agent</a> with enhanced memory architecture, structured skill framework, and Manus-style persistent planning.**

---

## What's Different in This Fork

This fork layers four major enhancements on top of Hermes Agent:

### 🧠 Privacy-First Persistent Memory Stack

Three complementary memory systems, each purpose-built:

| System | Engine | Best For | Privacy |
|--------|--------|----------|---------|
| **SimpleMem** | LanceDB + SiliconFlow | Long-term context, cross-session recall | `<private>` tags auto-stripped |
| **Sirchmunk** | DuckDB + ripgrep | Full-text search across project history | Local-only, no cloud |
| **llm-wiki-agent** | litellm | Structured wiki-style knowledge base | Per-agent index |

All three run locally. Embeddings go through SiliconFlow (`BAAI/bge-large-zh-v1.5`, 1024d) when HuggingFace is unreachable.

### 📋 Manus-Style Task Planning

Integrated **planning-with-files** (19.3k ⭐ upstream) — the same pattern behind Meta's $2B Manus acquisition. Three persistent markdown files survive context loss and session resets:

```
task_plan.md   — Phase-based roadmap with status tracking
findings.md    — Research, discoveries, external content
progress.md    — Timestamped session log
```

5-phase workflow (Requirements → Planning → Implementation → Testing → Delivery) with automatic phase status management. 2-Action Rule prevents multimodal information loss.

### 🏗️ RIA-TV++ Skill Framework

17 core software-development skills upgraded to **RIA-TV++ v2.0.0** structured format:

- `systematic-debugging` — 闭环调试协议
- `test-driven-development` — TDD + verification gates
- `planning-and-task-breakdown` — 结构化任务分解
- `requesting-code-review` — 增量式代码审查
- `incremental-implementation` — 小步增量交付
- `code-simplification` — 递归代码简化
- `subagent-driven-development` — 并行子代理编排
- `spec-driven-development` — 规范先行开发
- `source-driven-development` — 源码优先溯源
- `writing-plans` — 多层级规划写作
- `idea-refine` — 约束驱动创意精化
- `context-engineering` — 上下文工程
- `hermes-agent-architecture` — Hermes 架构深度理解
- `hermes-evolver-integration` — Self-evolution 集成

Each skill follows the R/I/A1/A2/E/B six-section structure with explicit execution steps, boundary conditions, and trigger scenarios.

### 🔄 Self-Evolution Loop

Hermes Agent's built-in learning loop supercharged:

- **Evolver integration** — `skills-evolution-from-research` skill continuously evaluates and integrates external research
- **Skills auto-improve** — complex tasks trigger skill upgrades with verified workflows
- **Cross-session memory** — FTS5 session search with LLM summarization recalls decisions across sessions
- **Memory persistence** — agent nudges itself to write memories after significant work

---

## Core Features (from upstream)

<table>
<tr><td><b>Any model, any provider</b></td><td>Nous Portal, OpenRouter (200+ models), NVIDIA NIM, Xiaomi MiMo, Kimi/Moonshot, MiniMax, Hugging Face, OpenAI, or any OpenAI-compatible endpoint. Switch with <code>hermes model</code>.</td></tr>
<tr><td><b>Multi-platform messaging</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal, Email — all from one gateway process. Talk from your phone while it works on a cloud VM.</td></tr>
<tr><td><b>Full terminal interface</b></td><td>Multiline editing, slash commands with autocomplete, conversation history, interrupt-and-redirect, streaming tool output.</td></tr>
<tr><td><b>Cron scheduling</b></td><td>Natural-language task scheduling with delivery to any platform. Daily reports, nightly audits, weekly summaries.</td></tr>
<tr><td><b>Parallel subagents</b></td><td>Spawn isolated subagents for concurrent workstreams. Zero-context-cost inter-agent communication.</td></tr>
<tr><td><b>Runs anywhere</b></td><td>Local, Docker, SSH, Daytona, Singularity, Modal. Modal/Daytona hibernate when idle — near-zero cost between sessions.</td></tr>
</table>

---

## Quick Start

```bash
# Install (Linux, macOS, WSL2)
curl -fsSL https://raw.githubusercontent.com/Nazicc/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc    # or ~/.zshrc
hermes              # start chatting!
```

```bash
# Or clone and develop
git clone https://github.com/Nazicc/hermes-agent.git
cd hermes-agent
./setup-hermes.sh
```

After install:

```bash
hermes              # Interactive CLI
hermes model        # Choose LLM provider + model
hermes setup        # Full setup wizard
hermes gateway      # Start messaging gateway
hermes doctor       # Diagnose issues
```

---

## Memory Systems At a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                    Hermes Memory Stack                       │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  SimpleMem   │   Sirchmunk   │ llm-wiki-agent│   claude-mem │
│  (LanceDB)   │   (DuckDB)    │   (litellm)   │  (privacy)   │
├──────────────┼──────────────┼──────────────┼───────────────┤
│ Cross-session│ Project-wide  │ Structured   │ <private> tag  │
│ long-term    │ full-text    │ wiki-style   │ stripping     │
│ context      │ search       │ knowledge    │               │
└──────────────┴──────────────┴──────────────┴───────────────┘
```

**MiniMax integration** — Configure in `~/.hermes/.env`:
```bash
OPENAI_API_KEY=sk-cp-your-key-here
OPENAI_BASE_URL=https://api.minimaxi.com/v1
LLM_MODEL=MiniMax-M2.7
```

---

## Skill System

Browse available skills:
```bash
hermes skills              # List all skills
hermes skills --search     # Search skills by keyword
/hermes                    # Load a specific skill
```

Create new skills:
```bash
/hermes create-skill       # Interactive skill creation
```

Skills persist in `~/.hermes/skills/` and are loaded automatically based on task context.

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Memory Architecture](docs/user-guide/features/memory) | SimpleMem, Sirchmunk, llm-wiki-agent — when to use each |
| [Skills System](docs/user-guide/features/skills) | RIA-TV++ format, creation workflow, self-improvement |
| [Planning Workflow](skills/productivity/planning-with-files) | Manus-style file-based task planning |
| [Cron Scheduling](docs/user-guide/features/cron) | Scheduled automations with platform delivery |
| [MCP Integration](docs/user-guide/features/mcp) | Connect any MCP server |
| [CLI Reference](docs/reference/cli-commands) | All commands and flags |

---

## Directory Structure (This Fork)

```
hermes-agent/
├── skills/
│   ├── software-development/     # 17 RIA-TV++ v2.0.0 skills
│   ├── productivity/
│   │   ├── planning-with-files/  # Manus-style planning (upstream 19.3k⭐)
│   │   ├── mem-search/           # Three-layer memory search protocol
│   │   └── llm-wiki-agent/       # Wiki knowledge base (litellm)
│   └── ...
├── docs/
│   ├── cangjie-skill-fusion-report.md      # RIA-TV++ methodology
│   ├── claude-mem-design-insights.md       # Privacy-first design
│   └── ...
└── README.md                    # This file
```

---

## License

MIT — same as upstream.

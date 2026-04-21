# Hermes Agent ☤

<p align="center">
  <img src="assets/banner.png" alt="Hermes Agent" width="100%">
</p>
<p align="center">
  <a href="https://github.com/Nazicc/hermes-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://github.com/Nazicc/hermes-agent"><img src="https://img.shields.io/badge/Stars-19.3k-orange?style=for-the-badge" alt="Stars"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
</p>

**[English](#whats-different-in-this-fork) · [中文](#此分支有何不同)](#此分支有何不同)**

---

## What's Different in This Fork

## 此分支有何不同

---

This fork layers four major enhancements on top of Hermes Agent:

本分支在 Hermes Agent 基础上叠加了四大核心增强：

### 🧠 Privacy-First Persistent Memory Stack

### 🧠 隐私优先的持久化记忆架构

---

Three complementary memory systems, each purpose-built:

三套互补的记忆系统，各司其职：

| System 系统 | Engine 引擎 | Best For 适用场景 | Privacy 隐私 |
|------------|-------------|-------------------|-------------|
| **SimpleMem** | LanceDB + SiliconFlow | Long-term context, cross-session recall 长期上下文、跨会话记忆 | `<private>` tags auto-stripped `<private>` 标签自动清除 |
| **Sirchmunk** | DuckDB + ripgrep | Full-text search across project history 项目历史全文检索 | Local-only, no cloud 纯本地，无云端 |
| **llm-wiki-agent** | litellm | Structured wiki-style knowledge base 结构化 Wiki 知识库 | Per-agent index 每 Agent 独立索引 |

All three run locally. Embeddings go through SiliconFlow (`BAAI/bge-large-zh-v1.5`, 1024d) when HuggingFace is unreachable.

三套系统均本地运行。HuggingFace 无法访问时，嵌入模型通过 SiliconFlow（`BAAI/bge-large-zh-v1.5`，1024 维）绕道。

---

### 📋 Manus-Style Task Planning

### 📋 Manus 风格任务规划

---

Integrated **planning-with-files** (19.3k ⭐ upstream) — the same pattern behind Meta's $2B Manus acquisition. Three persistent markdown files survive context loss and session resets:

集成 **planning-with-files**（上游 19.3k ⭐）— 这正是 Meta 以 20 亿美元收购 Manus 背后的核心模式。三份持久化 Markdown 文件在上下文丢失和会话重置中存活：

```
task_plan.md   — Phase-based roadmap with status tracking  阶段性路线图，带状态跟踪
findings.md    — Research, discoveries, external content   调研、发现、外部内容
progress.md    — Timestamped session log                   带时间戳的会话日志
```

5-phase workflow (Requirements → Planning → Implementation → Testing → Delivery) with automatic phase status management. 2-Action Rule prevents multimodal information loss.

五阶段工作流（需求 → 规划 → 实现 → 测试 → 交付），自动管理阶段状态。二动作规则防止多模态信息丢失。

---

### 🏗️ RIA-TV++ Skill Framework

### 🏗️ RIA-TV++ 技能框架

---

17 core software-development skills upgraded to **RIA-TV++ v2.0.0** structured format:

17 个核心软件开发技能已升级至 **RIA-TV++ v2.0.0** 结构化格式：

| Skill | Description 描述 |
|-------|-----------------|
| `systematic-debugging` | 闭环调试协议 |
| `test-driven-development` | TDD + verification gates 验证门控 |
| `planning-and-task-breakdown` | 结构化任务分解 |
| `requesting-code-review` | 增量式代码审查 |
| `incremental-implementation` | 小步增量交付 |
| `code-simplification` | 递归代码简化 |
| `subagent-driven-development` | 并行子代理编排 |
| `spec-driven-development` | 规范先行开发 |
| `source-driven-development` | 源码优先溯源 |
| `writing-plans` | 多层级规划写作 |
| `idea-refine` | 约束驱动创意精化 |
| `context-engineering` | 上下文工程 |
| `hermes-agent-architecture` | Hermes 架构深度理解 |
| `hermes-evolver-integration` | Self-evolution 集成 |
| `hermes-eval` | Skill 自动化评测框架（Eval Harness + 14 个 suites） |
| `simplestorage-adapter` | SimpleMem 存储后端适配器（PostgreSQL/pgvector） |

Each skill follows the R/I/A1/A2/E/B six-section structure with explicit execution steps, boundary conditions, and trigger scenarios.

每项技能遵循 R/I/A1/A2/E/B 六段式结构，含明确执行步骤、边界条件和触发场景。

---

### 🔄 Self-Evolution Loop

### 🔄 自我进化循环

---

Hermes Agent's built-in learning loop supercharged:

对 Hermes Agent 内置学习循环的全面增强：

- **Evolver integration** — `skills-evolution-from-research` skill continuously evaluates and integrates external research
- **Evolver 集成** — `skills-evolution-from-research` 技能持续评估并整合外部研究
- **Skills auto-improve** — complex tasks trigger skill upgrades with verified workflows
- **技能自动进化** — 复杂任务触发技能升级，带验证工作流
- **Eval Harness** — `hermes-eval` 评测框架，14 个 suite，升级前必须 PASS（score ≥ 80%）
- **Cross-session memory** — FTS5 session search with LLM summarization recalls decisions across sessions
- **跨会话记忆** — FTS5 会话搜索 + LLM 摘要，跨会话召回决策
- **Memory persistence** — agent nudges itself to write memories after significant work
- **记忆持久化** — Agent 在重要工作后主动写记忆

---

## Core Features (from upstream)

## 核心功能（来自上游）

---

<table>
<tr><th>Feature 功能</th><th>Description 描述</th></tr>
<tr><td><b>Any model, any provider</b></td><td>Nous Portal, OpenRouter (200+ models), NVIDIA NIM, Xiaomi MiMo, Kimi/Moonshot, MiniMax, Hugging Face, OpenAI, or any OpenAI-compatible endpoint. Switch with <code>hermes model</code>.</td></tr>
<tr><td><b>任意模型，任意提供商</b></td><td>Nous Portal、OpenRouter（200+ 模型）、NVIDIA NIM、小米 MiMo、Kimi/Moonshot、MiniMax、Hugging Face、OpenAI 或任何 OpenAI 兼容端点。用 <code>hermes model</code> 切换。</td></tr>
<tr><td colspan="2">&nbsp;</td></tr>
<tr><td><b>Multi-platform messaging</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal, Email — all from one gateway process. Talk from your phone while it works on a cloud VM.</td></tr>
<tr><td><b>多平台消息</b></td><td>Telegram、Discord、Slack、WhatsApp、Signal、Email — 一个网关进程搞定。在手机上聊天，同时在云 VM 上工作。</td></tr>
<tr><td colspan="2">&nbsp;</td></tr>
<tr><td><b>Full terminal interface</b></td><td>Multiline editing, slash commands with autocomplete, conversation history, interrupt-and-redirect, streaming tool output.</td></tr>
<tr><td><b>全功能终端界面</b></td><td>多行编辑、带自动补全的斜杠命令、对话历史、打断重定向、流式工具输出。</td></tr>
<tr><td colspan="2">&nbsp;</td></tr>
<tr><td><b>Cron scheduling</b></td><td>Natural-language task scheduling with delivery to any platform. Daily reports, nightly audits, weekly summaries.</td></tr>
<tr><td><b>定时任务调度</b></td><td>自然语言任务调度，支持投递到任意平台。日报告、夜间审计、周总结。</td></tr>
<tr><td colspan="2">&nbsp;</td></tr>
<tr><td><b>Parallel subagents</b></td><td>Spawn isolated subagents for concurrent workstreams. Zero-context-cost inter-agent communication.</td></tr>
<tr><td><b>并行子代理</b></td><td>派生隔离子代理并发工作。零上下文开销的代理间通信。</td></tr>
<tr><td colspan="2">&nbsp;</td></tr>
<tr><td><b>Runs anywhere</b></td><td>Local, Docker, SSH, Daytona, Singularity, Modal. Modal/Daytona hibernate when idle — near-zero cost between sessions.</td></tr>
<tr><td><b>任意环境运行</b></td><td>本地、Docker、SSH、Daytona、Singularity、Modal。Modal/Daytona 空闲时休眠 — 会话间几乎零成本。</td></tr>
</table>

---

## Quick Start

## 快速上手

---

```bash
# Install (Linux, macOS, WSL2)
# 安装（Linux、macOS、WSL2）
curl -fsSL https://raw.githubusercontent.com/Nazicc/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc    # or ~/.zshrc
hermes              # start chatting! 开始聊天！
```

```bash
# Or clone and develop
# 或克隆并开发
git clone https://github.com/Nazicc/hermes-agent.git
cd hermes-agent
./setup-hermes.sh
```

After install / 安装后：

```bash
hermes              # Interactive CLI 交互式 CLI
hermes model        # Choose LLM provider + model 选择 LLM 提供商和模型
hermes setup        # Full setup wizard 完整设置向导
hermes gateway      # Start messaging gateway 启动消息网关
hermes doctor       # Diagnose issues 诊断问题
```

---

## Memory Systems At a Glance

## 记忆系统一览

---

```
┌────────────────────────────────────────────────────────────────┐
│                    Hermes Memory Stack                          │
│                    Hermes 记忆架构                              │
├──────────────┬──────────────┬───────────────┬─────────────────┤
│  SimpleMem   │   Sirchmunk   │ llm-wiki-agent│   claude-mem   │
│  (LanceDB)   │   (DuckDB)    │   (litellm)   │  (privacy)     │
├──────────────┼──────────────┼───────────────┼─────────────────┤
│ Cross-session│ Project-wide  │ Structured    │ <private> tag  │
│ long-term    │ full-text     │ wiki-style    │ stripping      │
│ context      │ search        │ knowledge     │                │
│ 跨会话       │ 项目全局      │ 结构化        │ <private>      │
│ 长期上下文   │ 全文检索      │ Wiki 知识库   │ 标签清除       │
└──────────────┴──────────────┴───────────────┴─────────────────┘
```

**MiniMax integration** — Configure in `~/.hermes/.env`:

**MiniMax 集成** — 在 `~/.hermes/.env` 中配置：

```bash
OPENAI_API_KEY=***
OPENAI_BASE_URL=https://api.minimaxi.com/v1
LLM_MODEL=MiniMax-M2.7
```

---

## Skill System

## 技能系统

---

Browse available skills / 浏览可用技能：

```bash
hermes skills              # List all skills 列出所有技能
hermes skills --search     # Search skills by keyword 按关键词搜索技能
/hermes                    # Load a specific skill 加载特定技能
```

Create new skills / 创建新技能：

```bash
/hermes create-skill       # Interactive skill creation 交互式技能创建
```

Skills persist in `~/.hermes/skills/` and are loaded automatically based on task context.

技能保存在 `~/.hermes/skills/`，根据任务上下文自动加载。

---

## Documentation

## 文档

---

| Guide 指南 | Description 描述 |
|-----------|-----------------|
| [Memory Architecture](docs/user-guide/features/memory) | SimpleMem, Sirchmunk, llm-wiki-agent — when to use each / 各系统适用场景 |
| [Skills System](docs/user-guide/features/skills) | RIA-TV++ format, creation workflow, self-improvement / 格式、创建工作流、自我进化 |
| [Planning Workflow](skills/productivity/planning-with-files) | Manus-style file-based task planning / Manus 风格文件任务规划 |
| [Cron Scheduling](docs/user-guide/features/cron) | Scheduled automations with platform delivery / 定时自动化与平台投递 |
| [MCP Integration](docs/user-guide/features/mcp) | Connect any MCP server / 连接任意 MCP 服务器 |
| [CLI Reference](docs/reference/cli-commands) | All commands and flags / 所有命令和参数 |

---

## Directory Structure (This Fork)

## 目录结构（本分支）

---

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

## 许可证

MIT — same as upstream. / MIT — 与上游相同。

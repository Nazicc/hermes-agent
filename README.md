# Hermes Agent ☤ — Fork by Nazicc

<p align="center">
  <a href="https://github.com/Nazicc/hermes-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://github.com/Nazicc/hermes-agent"><img src="https://img.shields.io/badge/Stars-19.3k-orange?style=for-the-badge" alt="Stars"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
</p>

**[English](#whats-different-in-this-fork) · [中文](#此分支有何不同)**

---

## What's Different in This Fork

本 fork 在 Hermes Agent（NousResearch）基础上叠加了四大核心增强，同时保持与上游完全兼容。所有改动均在本地 `~/.hermes/` 运行时目录生效，git 仓库本身不携带任何 secret。

---

### 🛡️ 安全优先的开发规范

| 机制 | 说明 |
|------|------|
| **pre-commit hook** | 提交前扫描 `sk-`(32+字符)、`ghp_`(36+字符) 等 secret 模式，匹配则阻断 |
| **post-commit hook** | 每次 `git commit` 自动 `make deploy` 同步 prerun scripts |
| **Makefile** | `make setup` / `make deploy` / `make test` 一键环境恢复 |
| **敏感信息安全** | 所有 API key/token 只在运行时通过 memory 注入，从不写入文件 |

```bash
# 新机器 clone 后一键恢复
make setup          # 安装 hooks + 部署 prerun scripts
make test           # 运行全部 cron 测试
```

---

### 🧠 Privacy-First Persistent Memory Stack

三套互补的记忆系统，均本地运行：

| System | Engine | Best For | Privacy |
|--------|--------|----------|---------|
| **SimpleMem** | LanceDB + SiliconFlow | 跨会话长期上下文召回 | `<private>` 标签自动清除 |
| **Sirchmunk** | DuckDB + ripgrep | 项目历史全文检索 | 纯本地，无云端 |
| **llm-wiki-agent** | litellm | 结构化 Wiki 知识库 | 每 Agent 独立索引 |

Embeddings 通过 SiliconFlow（`BAAI/bge-large-zh-v1.5`，1024维）当 HuggingFace 不可达时绕道。

---

### 📋 Manus-Style Task Planning

集成 **planning-with-files**（上游 19.3k ⭐）。三份持久化 Markdown 在上下文丢失和会话重置中存活：

```
task_plan.md   — 阶段性路线图，带状态跟踪
findings.md    — 调研、发现、外部内容
progress.md    — 带时间戳的会话日志
```

五阶段工作流（需求 → 规划 → 实现 → 测试 → 交付），自动管理阶段状态。二动作规则防止多模态信息丢失。

---

### 🏗️ RIA-TV++ Skill Framework

17 个核心软件开发技能已升级至 **RIA-TV++ v2.0.0** 结构化格式：

`systematic-debugging` · `test-driven-development` · `planning-and-task-breakdown` · `requesting-code-review` · `incremental-implementation` · `code-simplification` · `subagent-driven-development` · `spec-driven-development` · `source-driven-development` · `writing-plans` · `idea-refine` · `context-engineering` · `hermes-agent-architecture` · `hermes-evolver-integration` · `hermes-eval` · `simplestorage-adapter` · `dogfood`

每项技能遵循 **R/I/A1/A2/E/B** 六段式结构（Trigger · Situation · Action · Verification · Edge Cases · Best Practices），含明确执行步骤、边界条件和触发场景。

Skills 质量评测框架：**71 tests，8 MCP tools**，升级前必须 PASS（score ≥ 80%）。

---

### 🔄 Self-Evolution Loop

- **Evolver 集成** — `skills-evolution-from-research` 技能持续评估并整合外部研究
- **技能自动进化** — 复杂任务触发技能升级，带验证工作流
- **Eval Harness** — 14 个评测 suite，升级前必须 PASS
- **跨会话记忆** — FTS5 会话搜索 + LLM 摘要，跨会话召回决策
- **Topic-change guard** — `_TopicTracker` 在每次 prefetch 前做 token overlap 检测（阈值 0.6），新话题跳过 prefetch

---

### ⏰ Cron Job System with RSS Health Intelligence

定时任务调度系统，支持 prerun script 预检 + 多平台投递（飞书/Telegram/Email）：

| 功能 | 说明 |
|------|------|
| **Prerun Script** | 任务执行前运行数据收集脚本，stdout 注入 prompt |
| **RSS Health Checker** | 并发检查 6 个 RSS 源，分类：healthy / degraded / waf_blocked / http_error / timeout / unreachable |
| **飞书投递** | 安全资讯日报每日 08:30 自动推送到飞书 |

当前活跃 cron job：
- **安全资讯日报**（`5bed6f2e3557`）— 每日 08:30，预检 RSS 源健康状态

```bash
# 手动运行 RSS 健康检查
python3 ~/.hermes/scripts/rss_health_checker.py --json
```

---

## Core Features（来自上游）

| Feature | Description |
|---------|-------------|
| **Any model, any provider** | Nous Portal、OpenRouter（200+ 模型）、NVIDIA NIM、MiniMax、Hugging Face、OpenAI 或任何 OpenAI 兼容端点 |
| **Multi-platform messaging** | Telegram、Discord、Slack、WhatsApp、Signal、Email，一个网关进程 |
| **Full terminal interface** | 多行编辑、斜杠命令自动补全、对话历史、流式工具输出 |
| **Parallel subagents** | 派生隔离子代理并发工作，零上下文开销 |
| **Runs anywhere** | 本地、Docker、SSH、Daytona、Singularity、Modal |

---

## Quick Start

```bash
# 安装
curl -fsSL https://raw.githubusercontent.com/Nazicc/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc    # or ~/.zshrc
hermes              # 开始聊天

# 开发 clone
git clone https://github.com/Nazicc/hermes-agent.git
cd hermes-agent
./setup-hermes.sh

# 新机器恢复（必须）
make setup          # 安装 git hooks + 部署 prerun scripts

# 常用命令
hermes              # 交互式 CLI
hermes model        # 选择 LLM 提供商和模型
hermes gateway      # 启动消息网关
hermes doctor       # 诊断问题
make test           # 运行全部测试
make deploy         # 同步 prerun scripts
```

**MiniMax 集成** — 在 `~/.hermes/.env` 中配置：

```bash
OPENAI_API_KEY=sk-cp-xxx          # Token Plan Key（sk-cp- 前缀）
OPENAI_BASE_URL=https://api.minimaxi.com/anthropic
LLM_MODEL=MiniMax-M2.7
```

---

## 目录结构

```
hermes-agent/
├── Makefile                        # make setup / deploy / test
├── scripts/
│   ├── git-hooks/
│   │   ├── pre-commit              # 敏感信息扫描（secret scanner）
│   │   └── post-commit             # 自动 make deploy
│   └── deploy_prerun.sh            # prerun script 同步脚本
├── cron/
│   ├── rss_health_checker.py       # RSS 源健康检查（BTT/TDD，19 测试）
│   ├── SPEC_rss_health_checker.md  # BDD feature spec
│   ├── scheduler.py                # cron 调度器（含 prerun script 机制）
│   ├── jobs.py                     # job CRUD（~/.hermes/cron/jobs.json）
│   └── tests/
│       └── test_rss_health_checker.py
├── skills/                         # RIA-TV++ v2.0.0 技能（17 核心 + 更多）
│   ├── software-development/
│   └── productivity/
│       └── planning-with-files/    # Manus 风格任务规划
├── hermes_state.py                 # SQLite（cron 状态 + 执行历史 + agents）
└── hermes-agent-self-evolution/   # DSPy + GEPA 自我进化引擎
```

---

## Changelog

<!-- 日志由每日 23:00 cron 自动生成，请勿手动修改此区块 -->

#### 2026-04-25
- `f2930b11` feat(security): add pre-commit secret scanner + post-commit auto-deploy hooks
- `60441f99` feat(cron): add Makefile + deploy script for prerun sync
- `de36e3fc` feat(cron): add RSS source health checker — BDD/TDD (19 tests passing)
- `67195ed0` feat(skills_quality): Hermes Skills Quality Framework — 71 tests, 8 MCP tools
- `3794adf9` feat(skills): add 8 research-driven skills (BDI, context compression/degradation/fundamentals, latent briefing, memory systems, multi-agent patterns, tool design)

#### 2026-04-23
- `6f3633a8` docs(hermes-agent): add critical operational paths and execute_code sandbox warning

<!-- CHANGELOG_MARKER -->

---

## License

MIT — same as upstream.

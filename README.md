# Hermes Agent ☤ — Fork by Nazicc

<p align="center">
  <a href="https://github.com/Nazicc/hermes-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://github.com/Nazicc/hermes-agent"><img src="https://img.shields.io/badge/Stars-19.3k-orange?style=for-the-badge" alt="Stars"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
</p>

**[English](#whats-different-in-this-fork) · [中文](#此分支有何不同)**

---

## 此分支有何不同

本 fork 在 Hermes Agent（NousResearch）基础上叠加了四大核心增强，同时保持与上游完全兼容。所有改动均在本地 `~/.hermes/` 运行时目录生效。

---

### 🛡️ 安全优先的开发规范

| 机制 | 说明 |
|------|------|
| **pre-commit hook** | 提交前扫描 `sk-(32+字符)`、`ghp_(36+字符)` 等 secret 模式，匹配则阻断 |
| **post-commit hook** | 每次 `git commit` 自动 `make deploy` 同步 prerun scripts |
| **Makefile** | `make setup` / `make deploy` / `make test` 一键环境恢复 |
| **敏感信息安全** | 所有 API key 只通过环境变量引用，从不硬编码写入配置文件 |

---

### 🤖 三套 Agent 调度体系

| Agent | 能力 | 适用场景 |
|-------|------|---------|
| **DeerFlow** | 深度研究、Web 搜索、多步骤推理、21 内置 skills | 复杂调研任务、流式思考过程 |
| **DeepCode** | 任务规划、论文转代码、需求分析、工作流状态管理 | 代码生成、架构设计、paper 实现 |
| **DeepTutor** | 知识库 RAG、TutorBot 自定义教学、Co-Writer 交互学习 | 学习辅导、知识管理、问答笔记 |

**调度规则**：代码/架构 → DeepCode；知识/教学 → DeepTutor；深度研究 → DeerFlow；本地文件 → SirchMunk；RAG 知识库 → OpenViking

---

### 🧠 Privacy-First Persistent Memory Stack

三套互补的记忆系统，均本地运行：

| System | Engine | Best For | Privacy |
|--------|--------|----------|---------|
| **SimpleMem** | LanceDB + embedding | 跨会话长期上下文召回 | 遗忘曲线 + 权重衰减 |
| **Hindsight** | Docker + 多策略召回 | 经验记忆、洞察反思、情景记忆 | bank 隔离，纯本地 |
| **Sirchmunk** | DuckDB + ripgrep | 项目历史全文检索 | 纯本地，无云端 |
| **OpenViking** | RAG pipeline | 结构化知识库问答 | 本地知识库，直连工具 |

---

### 📋 Manus-Style Task Planning

集成 **planning-with-files**。三份持久化 Markdown 在上下文丢失和会话重置中存活：

```
task_plan.md   — 阶段性路线图，带状态跟踪
findings.md    — 调研、发现、外部内容
progress.md    — 带时间戳的会话日志
```

---

### 🔄 Self-Evolution Loop

- **Evolver 集成** — `skills-evolution-from-research` 技能持续评估并整合外部研究
- **技能自动进化** — 复杂任务触发技能升级，带验证工作流
- **跨会话记忆** — FTS5 会话搜索 + LLM 摘要，跨会话召回决策

---

### 🏗️ RIA-TV++ Skill Framework

**67 个技能** 覆盖软件开发、研究、MLOps、生产力等场景，核心技能：

`systematic-debugging` · `test-driven-development` · `incremental-implementation` · `spec-driven-development` · `source-driven-development` · `requesting-code-review` · `subagent-driven-development` · `planning-with-files` · `context-engineering` · `deerflow-mcp-integration` · `native-mcp` · `hermes-agent-architecture` · `hermes-evolver-integration` · `hermes-daily-maintenance` · `deepcode-research-engine` · `github-code-review` · `pytorch-fsdp` · `peft` · `axolotl` · `unsloth` · `vllm`

---

## 系统架构

```
                         用户（飞书 / CLI）
                                   │
                        ┌──────────▼───────────┐
                        │   Hermes Gateway      │
                        │   run.py              │
                        └──────────┬───────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
    ┌──────────▼──┐       ┌─────────▼──────┐    ┌───────▼──────┐
    │ SkillClaw   │       │ MCP Client     │    │  Evolver     │
    │ :30000      │       │ (stdio bridge) │    │  Engine      │
    │ (relay)     │       └───────┬────────┘    └─────────────┘
    └─────┬──────────────┬────────┼───────────────────────┘
          │              │       │
   ┌──────▼──────┐ ┌─────▼──────▼──────┐
   │ deerflow-mcp │ │ deepcode-mcp       │ deeptutor-mcp
   │ :1933        │ │ deepcode-mcp/      │ deeptutor-mcp/
   └──────┬──────┘ └──────┬─────────────┘ └──────┬──────────┘
          │              │                        │
          ▼              ▼                        ▼
   DeerFlow langgraph DeepCode backend      DeepTutor backend
   (via SkillClaw)  :8000 (FastAPI)         :8001 (FastAPI)
                         │                        │
                        ▼                        ▼
                 MiniMax M2.7              MiniMax M2.7
             api.minimaxi.com/anthropic  api.minimaxi.com/anthropic

   MCP stdio servers: sirchmunk · simplemem · simplemem_evo · skills-quality

   macOS launchd services (launchd/):
     DeerFlow MCP · DeepCode backend/frontend · DeepTutor backend/frontend
     OpenViking :1934 · SirchMunk · SkillClaw health/proxy
```

---

## 核心组件路径

| 组件 | 路径 |
|------|------|
| hermes-agent 源码 | `~/.hermes/hermes-agent/` |
| Skills | `~/.hermes/skills/skills/` (67) |
| SkillClaw | `~/.hermes/SkillClaw/` |
| DeerFlow repo | `~/.hermes/deer-flow-repo/` |
| DeepCode 后端 | `~/DeepCode/` |
| DeepTutor 后端 | `~/.hermes/DeepCode/DeepTutor/` |
| MCP servers | `~/.hermes/hermes-agent/mcp-servers/` |
| OpenViking | `~/.hermes/openviking/` |
| SirchMunk | `~/.hermes/sirchmunk/` |
| cron scripts | `~/.hermes/scripts/` |
| Evolver | `~/.hermes/hermes-agent/evolver/` |

---

## 快速开始

```bash
# 交互式 CLI
hermes

# 诊断
hermes doctor

# MCP 管理
hermes mcp list
hermes mcp test deerflow

# 新机器恢复
make setup          # 安装 git hooks + 部署 prerun scripts
make deploy         # 同步 prerun scripts
make test           # 运行全部测试
```

### MiniMax 配置

在 `~/.hermes/.env` 中配置：

```bash
MINIMAX_CN_API_KEY=***
MINIMAX_CN_BASE_URL=https://api.minimaxi.com/anthropic/v1
MINIMAX_CN_MODEL_NAME=MiniMax-M2.7
```

---

## Cron 定时任务

```bash
# 列出所有 cron jobs
hermes cron list

# 手动运行 RSS 健康检查
python3 ~/.hermes/scripts/rss_health_checker.py --json
```

---

## DeepCode / DeepTutor 使用示例

### DeepCode — 任务规划

```
→ deepcode_chat_planning(
    requirements="用 Python 实现一个支持并发连接的记忆系统，基于 LanceDB"
)
→ DeepCode 自动拆解为子任务、代码结构、技术选型
```

### DeepCode — 论文转代码

```
→ deepcode_paper_to_code(
    paper_url="https://arxiv.org/abs/...",
    input_type="url"
)
→ DeepCode 解析论文 + 生成完整代码实现
```

### DeepTutor — 创建学习助手

```
→ deeptutor_create_tutorbot(
    name="ML Tutor",
    soul="你是一位 ML 教授，擅长用生活案例解释复杂概念"
)
→ deeptutor_tutorbot_chat(bot_id="...", message="什么是 RAG？")
```

### DeerFlow — 深度研究

```
→ deerflow_chat(
    message="研究 2025 年 AI Agent 最新进展，给出结构化报告",
    thinking_enabled=true
)
→ DeerFlow 自动调用 web_search + web_fetch，输出带 citations 的报告
```

---

## 目录结构

```
hermes-agent/
├── Makefile                          # make setup / deploy / test
├── mcp-servers/                      # MCP stdio server 实现
│   ├── deerflow-mcp/                 # DeerFlow MCP 桥接
│   ├── deepcode-mcp/                 # DeepCode MCP 桥接
│   └── deeptutor-mcp/               # DeepTutor MCP 桥接
├── launchd/                           # macOS launchd plist 服务定义
│   ├── com.hermes.deerflow-mcp.plist
│   ├── com.hermes.deepcode-*.plist
│   ├── com.hermes.deeptutor-*.plist
│   ├── com.hermes.openviking.plist
│   ├── com.hermes.sirchmunk.plist
│   └── com.hermes.skillclaw-*.plist
├── scripts/
│   ├── git-hooks/
│   │   ├── pre-commit                # 敏感信息扫描
│   │   └── post-commit               # 自动 make deploy
│   └── deploy_prerun.sh
├── cron/
│   ├── rss_health_checker.py         # RSS 源健康检查
│   └── scheduler.py                  # 定时任务调度器
├── hermes_cli/                       # CLI 所有子命令
├── agent/                            # AIAgent 核心（prompt builder、context compressor、...)
├── tools/                             # 全部工具实现（50+）
├── gateway/                          # 消息平台网关（飞书/Telegram/Discord/...）
├── tui_gateway/                      # TUI JSON-RPC 后端
├── acp_adapter/                      # VS Code / Zed / JetBrains ACP 集成
├── skills_quality/                    # Skills 质量评分 MCP（8 tools, 71 tests）
├── evolver/                          # Self-evolution 引擎
└── tests/                            # pytest 测试套件（3000+ tests）
```

---

## Changelog

#### 2026-04-30
- `82dd9c5c` feat(evolver): add `--api-base` option to evolve_skill.py — enables custom LLM API base URL for DSPy LM (e.g. SkillClaw relay at localhost:30000)

#### 2026-04-29
- `3905e8b1` fix: normalize_usage dict-key fallback and MiniMax field aliases
- `3e442af6` fix: normalize_usage fallback for MiniMax/SkillClaw hybrid cache metric
- `5414cb29` feat: add openviking plist, deerflow runner, conversation records
- `596c5328` fix: skillclaw-proxy plist uses correct SkillClaw venv python path
- `675cdd57` feat: add launchd plists for DeerFlow/DeepCode/DeepTutor services
- `cd0bbf7e` feat: move all MCP server implementations into hermes-agent repo

#### 2026-04-28
- `375e66a3` docs: add DeerFlow MCP integration section to README
- `bf47944b` fix(cron): replace httpx with stdlib urllib in rss_health_checker
- `dda274fb` feat(memory): add ~/.hermes/agent_memory.md as third persistence anchor

#### 2026-04-25
- `e7fdd234` docs: rewrite README — fork identity, security hooks, cron health checker, RIA-TV++
- `f2930b11` feat(security): add pre-commit secret scanner + post-commit auto-deploy hooks

<!-- CHANGELOG_MARKER -->

---

## License

MIT — same as upstream.

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
| **敏感信息安全** | 所有 API key 只通过环境变量引用，从不硬编码写入配置文件 |

---

### 🔀 SkillClaw Proxy Layer

**SkillClaw** 是本地 LLM 流量代理层，运行于 `localhost:30000`，负责：

- **多租户路由**：MiniMax Token Plan Key + round_robin 负载策略
- **协议兼容**：OpenAI-compatible API，零成本切换模型
- **健康守护**：`skillclaw-health` launchd 持续监控，`ai.hermes.skillclaw-evolve` 处理自动进化
- **配置隔离**：`.env` 中存储所有 key，SkillClaw 只读环境变量

```
hermes-agent → SkillClaw (:30000) → MiniMax / OpenAI-compatible endpoints
```

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

五套互补的记忆系统，均本地运行：

| System | Engine | Best For | Privacy |
|--------|--------|----------|---------|
| **SimpleMem** | LanceDB + embedding | 跨会话长期上下文召回 | 遗忘曲线 + 权重衰减 |
| **SimpleMem Evolution** | Gene + WorkingMemory | 触发-动作规则、自动进化 | 记忆强化 + 衰减 |
| **Hindsight** | Docker (pgvector) + 多策略召回 | 经验记忆、洞察反思、情景记忆 | bank 隔离，纯本地 |
| **Sirchmunk** | DuckDB + ripgrep | 项目历史全文检索 | 纯本地，无云端 |
| **OpenViking** | Docker + RAG pipeline | 结构化知识库问答 | 本地知识库，直连工具 |

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
- **GEPA 优化** — DSPy + GEPA 算法驱动技能参数自动调优

---

### 🏗️ RIA-TV++ Skill Framework

**110 个技能** 覆盖软件开发、研究、MLOps、生产力等场景：

**核心开发**：`systematic-debugging` · `test-driven-development` · `incremental-implementation` · `spec-driven-development` · `source-driven-development` · `requesting-code-review` · `subagent-driven-development` · `planning-with-files` · `context-engineering`

**Agent 集成**：`deerflow-mcp-integration` · `deepcode-research-engine` · `hermes-evolver-integration` · `hermes-daily-maintenance` · `hermes-mcp-tdd-workflow` · `hermes-prerun-script-deploy`

**MLOps**：`pytorch-fsdp` · `peft` · `axolotl` · `unsloth` · `vllm` · `huggingface-hub` · `tensorrt-llm` · `torchtitan` · `accelerate`

**Agent 框架**：`autonomous-ai-agents` · `claude-code` · `opencode` · `blackbox` · `godmode`

**DevOps**：`docker-management` · `launchd-service-management` · `hermes-agent-cron-script-standards`

**RAG/知识**：`simplemem-mcp` · `simplemem-local-embedding` · `amp-typed-memory` · `simplestorage-adapter` · `qdrant` · `pinecone` · `chroma`

**安全**：`web-hacking-payloads` · `prompt-injection` · `vulnerability-intelligence` · `oss-forensics` · `git-history-security-response`

---

## 系统架构

```
                         用户（飞书 / CLI / API）
                                   │
                        ┌──────────▼───────────┐
                        │   Hermes Gateway      │
                        │   run.py              │
                        └──────────┬───────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
    ┌─────────▼────────┐  ┌────────▼────────┐  ┌─────────▼─────────┐
    │   AIAgent        │  │  MCP Client     │  │  Tool Registry   │
    │   run_agent.py   │  │  (~1050 行)      │  │  50+ 工具实现     │
    └─────────┬────────┘  └────────┬────────┘  └──────────────────┘
              │                   │
              │         ┌─────────┴──────────────────┐
              │         │  MCP Servers (8)            │
              │         ├─────────────────────────────┤
              │         │ sirchmunk      DuckDB 全文检索│
              │         │ simplemem      LanceDB + decay│
              │         │ simplemem_evo. Gene + WorkingM │
              │         │ skills-quality  技能质量评分  │
              │         │ deerflow       HKUDS 研究引擎│
              │         │ deepcode       任务规划+代码 │
              │         │ deeptutor      教学 + RAG    │
              │         │ hindsight      经验记忆 Docker│
              │         └─────────────────────────────┘
              │
    ┌─────────▼──────────────────┐     ┌──────────────────────┐
    │   SkillClaw Proxy          │ ←── │  OpenViking Docker   │
    │   localhost:30000          │     │  port 1934           │
    └─────────┬──────────────────┘     └──────────────────────┘
              │
    ┌─────────▼──────────────────┐
    │   MiniMax API             │
    │   Token Plan (sk-cp-...)  │  ← key 仅存于 ~/.hermes/.env
    └───────────────────────────┘
```

---

## 项目结构

```
~/.hermes/
├── config.yaml               # 主配置（API provider、toolsets、platforms、8个MCP server）
├── .env                      # 所有敏感密钥（.gitignore 排除）
├── SkillClaw/                # 本地 LLM 代理层
│   ├── skillclaw/            # 核心代理服务
│   ├── evolve_server/        # 自动进化服务
│   └── scripts/              # health-check 等运维脚本
├── hermes-agent/             # 主代码仓库（git 管理）
│   ├── run_agent.py          # AIAgent 核心
│   ├── model_tools.py        # 工具编排
│   ├── hermes_cli/           # CLI 所有子命令
│   ├── agent/                # prompt builder、context compressor、...
│   ├── tools/                # 50+ 工具实现
│   ├── gateway/              # 消息平台网关
│   ├── mcp-servers/          # 自定义 MCP 实现
│   │   ├── deerflow-mcp/
│   │   ├── deepcode-mcp/
│   │   └── deeptutor-mcp/
│   ├── skills_quality/       # Skills 质量评分 MCP
│   ├── hermes-agent-self-evolution/  # Self-evolution 引擎
│   └── tests/                # pytest 测试套件
├── skills/                   # 110 个技能目录
│   ├── skills/               # 核心技能（meta、architecture、...）
│   ├── optional-skills/      # 可选技能（MLOps、Docker、...）
│   ├── autonomous-ai-agents/ # 多 Agent 调度
│   ├── code-generation/      # DeepCode 集成
│   ├── mlops/                # 训练/推理工具
│   └── security/             # 安全研究技能
├── memories/                 # 记忆系统数据
│   ├── MEMORY.md             # 持久化 agent memory
│   └── USER.md               # 持久化用户 profile
├── simplemem-data/           # SimpleMem LanceDB 数据
├── simplemem_evolution/      # Evolution/Gene/WorkingMemory
├── sirchmunk-data/           # Sirchmunk DuckDB 数据
├── openviking-data/          # OpenViking RAG 数据
├── deer-flow-repo/           # DeerFlow 完整仓库
├── sessions/                  # SQLite 会话历史
├── state.db                  # Hermes 主状态库
├── cron/
│   ├── jobs.json             # 定时任务配置
│   └── output/               # 任务输出
├── scripts/
│   ├── skillclaw-health.sh   # SkillClaw 健康检查
│   ├── hindsight_mcp.py      # Hindsight MCP 入口
│   └── simplemem_mcp.py      # SimpleMem MCP 入口
└── launchd/                   # 9 个 launchd plist 服务
    ├── com.hermes.skillclaw-proxy.plist
    ├── com.hermes.skillclaw-health.plist
    ├── com.hermes.deepcode-backend.plist
    ├── com.hermes.deepcode-frontend.plist
    ├── com.hermes.deeptutor-backend.plist
    ├── com.hermes.deeptutor-frontend.plist
    ├── com.hermes.deerflow-mcp.plist
    ├── com.hermes.sirchmunk.plist
    └── com.hermes.openviking.plist
```

---

## 平台接入

| 平台 | 状态 | 说明 |
|------|------|------|
| **飞书** | ✅ 已接入 | Home channel: `oc_cb1804a2524577adba20634a65394b81` |
| **CLI** | ✅ | `hermes` 命令行入口 |
| **API Server** | ✅ | `127.0.0.1:8642`（key 认证） |
| **Telegram/Slack/Discord** | 配置 | `config.yaml` 中配置即可启用 |

---

## 定时任务

| Job | 触发 | 功能 |
|-----|------|------|
| **Daily Maintenance** | 04:00 | RSS 健康检查、memory flush、session 清理 |
| **hermes-agent-cron** | 覆写 | prerun 检查脚本同步 |
| **SkillClaw Health** | 持续 | SkillClaw 进程守护 |

---

## Changelog

#### 2026-05-01
- `a8a73690` chore: daily maintenance — web_server.py cleanup
- `8760f0d9` feat(skills): add security skills — web-hacking-payloads, prompt-injection, vulnerability-intelligence

#### 2026-04-30
- `222684aa` docs: add Hindsight to memory stack table
- `82dd9c5c` feat(evolver): add `--api-base` option — supports custom LLM API base URL for DSPy LM
- `c868383a` docs: update changelog

#### 2026-04-29
- `3905e8b1` fix: normalize_usage dict-key fallback and MiniMax field aliases
- `3e442af6` fix: normalize_usage fallback for MiniMax/SkillClaw hybrid cache metric
- `3e7055e7` chore: daily cleanup — memory refresh, session hygiene, openclaw artifacts cleared
- `549ea0c9` docs: update README — reflect current architecture (67 skills, 9 launchd services, mcp-servers/)

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

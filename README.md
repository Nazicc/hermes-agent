# Hermes Agent ☤ — Fork by Nazicc

<p align="center">
  <a href="https://github.com/Nazicc/hermes-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://github.com/Nazicc/hermes-agent"><img src="https://img.shields.io/badge/Stars-19.3k-orange?style=for-the-badge" alt="Stars"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
</p>

**English · 中文**

---

## 此分支有何不同

本 fork 在 Hermes Agent（NousResearch）基础上叠加了五大核心增强，同时保持与上游完全兼容。所有改动均在本地 `~/.hermes/` 运行时目录生效。

---

### 🛡️ 安全优先的开发规范

| 机制 | 说明 |
|------|------|
| **pre-commit hook** | 提交前扫描常见 secret 模式，匹配则阻断 |
| **post-commit hook** | 每次 `git commit` 自动 `make deploy` 同步 prerun scripts |
| **敏感信息安全** | 所有 API key 只通过环境变量引用，从不硬编码写入配置文件 |
| **.gitignore** | `.env`、`auth.json`、`state.db`、各类 `.pem`/`.ppk` 私钥、venv/ 均已排除 |

---

### 🔀 SkillClaw Proxy Layer

**SkillClaw** 是本地 LLM 流量代理层，运行于 `localhost:30000`，负责：

- **多租户路由**：Token Plan Key + round_robin 负载策略
- **协议兼容**：OpenAI-compatible API，零成本切换模型
- **健康守护**：`skillclaw-health` launchd 持续监控，自动故障转移
- **配置隔离**：`.env` 中存储所有 key，SkillClaw 只读环境变量

```
hermes-agent → SkillClaw (:30000) → MiniMax API
```

---

### 🤖 三套 Agent 调度体系

| Agent | 能力 | 适用场景 |
|-------|------|---------|
| **DeerFlow** | 深度研究、Web 搜索、多步骤推理、21 内置 skills | 复杂调研任务、流式思考过程 |
| **DeepCode** | 任务规划、论文转代码、需求分析、工作流状态管理 | 代码生成、架构设计、paper 实现 |
| **DeepTutor** | 知识库 RAG、TutorBot 自定义教学、Co-Writer 交互学习 | 学习辅导、知识管理、问答笔记 |

**调度规则**：代码/架构 → DeepCode；知识/教学 → DeepTutor；深度研究 → DeerFlow；本地文件 → SirchMunk；RAG 知识库 → OpenViking；个人知识图谱 → gbrain

---

### 🧠 Privacy-First Persistent Memory Stack

六套互补的记忆系统，均本地运行：

| System | Engine | Best For | Privacy |
|--------|--------|----------|---------|
| **SimpleMem** | LanceDB + embedding | 跨会话长期上下文召回 | 遗忘曲线 + 权重衰减 |
| **SimpleMem Evolution** | Gene + WorkingMemory | 触发-动作规则、自动进化 | 记忆强化 + 衰减 |
| **Hindsight** | Docker (pgvector) + 多策略召回 | 经验记忆、洞察反思、情景记忆 | bank 隔离，纯本地 |
| **SirchMunk** | DuckDB + ripgrep | 项目历史全文检索 | 纯本地，无云端 |
| **OpenViking** | Docker + RAG pipeline | 结构化知识库问答 | 本地知识库，直连工具 |
| **gbrain** | PGLite + BAAI/bge-large-zh-v1.5（SiliconFlow） | 知识图谱、RAG 语义搜索 | 纯本地，向量检索 |

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

### 🎯 CTF 综合能力

融合四大 CTF 知识库，构建互补的技能体系：

| 来源 | 内容 |
|------|------|
| **ctf-wiki** | 14 个方向完整理论知识（PWN/密码学/Web/逆向/杂项/区块链等） |
| **google-ctf** | 2017-2025 真实 CTF challenge（Docker/K8s 部署） |
| **awesome-ctf** | 工具链清单、平台索引、写作者社区 |
| **ctf-skills** | 实测可运行脚本模板（RSACTFTool/Pwntools/angr 等） |

**核心 CTF Skills**：`ctf-master`（综合入口）· `ctf-pwn`（PWN 深度）· `ctf-crypto-comprehensive`（密码学融合）· `ctf-skills-toolkit`（工具包）

---

### 🏗️ 189 Skills 技能体系

**189 个技能** 覆盖软件开发、研究、MLOps、生产力、安全等场景：

| 类别 | 代表技能 |
|------|---------|
| **软件开发** | `systematic-debugging` · `test-driven-development` · `incremental-implementation` · `spec-driven-development` · `source-driven-development` |
| **Agent 集成** | `deerflow-mcp-integration` · `deepcode-research-engine` · `hermes-evolver-integration` · `hermes-daily-maintenance` · `hermes-mcp-tdd-workflow` |
| **MLOps** | `pytorch-fsdp` · `peft` · `axolotl` · `unsloth` · `vllm` · `huggingface-hub` · `tensorrt-llm` · `torchtitan` |
| **图表生成** | `fireworks-tech-graph`（SVG+PNG 技术图，7 种风格） |
| **安全/CTF** | `oss-forensics` · `git-history-security-response` · `ctf-master` · `ctf-pwn` · `ctf-crypto-comprehensive` |
| **RAG/知识** | `simplemem-mcp` · `simplemem-local-embedding` · `amp-typed-memory` · `qdrant` · `pinecone` · `chroma` |

---

## 系统架构

![Architecture Diagram](architecture.svg)

```
                         用户（飞书 / CLI / API / Discord / ...）
                                       │
                        ┌──────────────▼──────────────┐
                        │      Hermes Gateway          │
                        │      run.py / cli.py         │
                        └──────────────┬──────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
┌─────────────▼──────────┐ ┌──────────▼──────────┐ ┌───────────▼───────────┐
│   AIAgent               │ │  MCP Client         │ │  Tool Registry        │
│   run_agent.py         │ │  (10 servers)       │ │  50+ 工具实现         │
│   ├─ prompt_builder    │ │  ├─ deerflow (:1933)│ │  ├─ terminal/file     │
│   ├─ context_compressor│ │  ├─ deepcode  (:8000)│ │  ├─ web/browse        │
│   ├─ memory_manager    │ │  ├─ deeptutor (:8001)│ │  ├─ vision/ocr       │
│   ├─ skill_commands    │ │  ├─ hindsight         │ │  ├─ delegation       │
│   └─ smart_routing     │ │  ├─ openviking (:1934)│ │  └─ ...             │
└─────────────────────────┘ └─────────────────────┘ └──────────────────────┘
                                       │
                         ┌─────────────┴──────────────┐
                         │    SkillClaw (:30000)        │
                         │    本地 LLM 代理 + 负载均衡   │
                         └─────────────┬──────────────┘
                         ┌─────────────▼──────────────┐
                         │   MiniMax API              │
                         └───────────────────────────┘

┌── MCP Servers ──────────────────────────────────────────────────────────┐
│  deerflow  → DeerFlow repo   │  deepcode → DeepCode :8000             │
│  deeptutor → DeepTutor :8001 │  hindsight  → Docker :18888 (pgvector) │
│  openviking→ Docker  :1934   │  gbrain     → Docker (PGLite+BAAI)     │
│  browser-harness → CDP :9222│  sirchmunk  → DuckDB+ripgrep           │
│  simplemem  → LanceDB+embed  │  simplemem_evo → Gene+WorkingMemory    │
│  skills-quality → 技能评分   │                                      │
└────────────────────────────────────────────────────────────────────────┘

┌── Memory Stack ─────────────────────────────────────────────────────────┐
│  SimpleMem · SimpleMem Evolution · Hindsight · SirchMunk ·             │
│  OpenViking · gbrain                                                    │
└────────────────────────────────────────────────────────────────────────┘

┌── Cron Jobs ────────────────────────────────────────────────────────────┐
│  04:00 每日系统维护  │ 08:30 安全资讯日报 │ */5min SkillClaw守护        │
│  240min 上下文健康  │ 0 */4h Evolver分析  │ 0 9 */3 Skills更新           │
│  0 9 * * 1 周升级   │ 0 23 * * * README推送                            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
~/.hermes/
├── config.yaml               # 主配置（API provider、toolsets、platforms、10个MCP server）
├── .env                      # 所有敏感密钥（.gitignore 排除，不上传）
├── hermes-agent/             # 主代码仓库（git 管理）
│   ├── run.py               # Gateway 入口
│   ├── cli.py               # CLI 入口（hermes 命令）
│   ├── run_agent.py         # AIAgent 核心（621K）
│   ├── agent/               # prompt builder、context compressor、memory manager...
│   ├── tools/               # 50+ 工具实现
│   ├── gateway/             # 消息平台网关（Feishu/Discord/Telegram/...）
│   ├── mcp-servers/         # 自定义 MCP 实现
│   │   ├── deerflow-mcp/
│   │   ├── deepcode-mcp/
│   │   ├── deeptutor-mcp/
│   │   └── browser-harness-mcp/
│   ├── skills_quality/      # Skills 质量评分 MCP
│   ├── hermes-agent-self-evolution/  # Self-evolution 引擎
│   ├── cron/                # Cron 预检脚本 + 测试
│   └── tests/               # pytest 测试套件
├── skills/                   # 189 个技能（41 个分类）
│   ├── ctf/                 # CTF 综合技能
│   ├── diagrams/            # fireworks-tech-graph（SVG+PNG 生成）
│   ├── mlops/               # 训练/推理工具
│   ├── security/            # 安全研究
│   ├── software-development/# 开发流程
│   └── ...
├── SkillClaw/               # 本地 LLM 代理层
├── deer-flow-repo/          # DeerFlow 完整仓库
├── deerflow-mcp/            # DeerFlow MCP 入口
├── deepcode-mcp/            # DeepCode MCP 入口
├── deeptutor-mcp/           # DeepTutor MCP 入口
├── scripts/
│   ├── rss_health_checker.py  # RSS 源健康检查
│   ├── hindsight_mcp.py       # Hindsight MCP 入口
│   ├── simplemem_mcp.py       # SimpleMem MCP 入口
│   └── skillclaw-health.sh    # SkillClaw 健康检查
├── memories/                  # 记忆系统数据
├── simplemem-data/           # SimpleMem LanceDB 数据
├── simplemem_evolution/       # Evolution/Gene/WorkingMemory
├── sirchmunk-data/           # SirchMunk DuckDB 数据
├── gbrain-data/              # gbrain PGLite 数据库（.gitignore 排除）
├── openviking-data/          # OpenViking RAG 数据
├── sessions/                 # SQLite 会话历史
├── state.db                  # Hermes 主状态库（.gitignore 排除）
├── cron/
│   ├── jobs.json            # 定时任务配置
│   └── output/              # 任务输出
├── launchd/                  # launchd plist 服务
│   ├── com.hermes.skillclaw-proxy.plist
│   ├── com.hermes.skillclaw-health.plist
│   ├── com.hermes.deepcode-backend.plist
│   ├── com.hermes.deepcode-frontend.plist
│   ├── com.hermes.deeptutor-backend.plist
│   ├── com.hermes.deeptutor-frontend.plist
│   ├── com.hermes.deerflow-mcp.plist
│   ├── com.hermes.sirchmunk.plist
│   └── com.hermes.openviking.plist
└── browser-harness-workspace/  # 浏览器自动化工作区
```

---

## 平台接入

| 平台 | 状态 | 说明 |
|------|------|------|
| **飞书** | ✅ 已接入 | 配置于 `config.yaml`，Home: `oc_cb1804a2524577adba20634a65394b81` |
| **CLI** | ✅ | `hermes` 命令行入口 |
| **API Server** | ✅ | localhost:8642（key 认证） |
| **Telegram/Slack/Discord** | 配置 | `config.yaml` 中配置即可启用 |

---

## 定时任务

| Job | 触发 | 功能 | 投递 |
|-----|------|------|------|
| **每日系统维护** | 04:00 | RSS 健康检查（5源）、agent 版本、代码兼容性、skills 审计 | origin |
| **安全资讯日报** | 08:30 | 抓取 5 个 RSS 源 → 每日安全摘要 | origin |
| **SkillClaw 路由守护** | */5min | launchd 进程守护，自动故障转移 | local |
| **上下文健康报告** | 240min | 会话摘要、记忆系统状态 | local |
| **Hermes-Evolver Bridge** | 0 */4h | session logs 同步、进化分析 | local |
| **Skills 更新与兼容性评估** | 0 9 */3 * | skills 目录扫描、兼容性测试 | origin |
| **hermes-weekly-upgrade** | 0 9 * * 1 | skills/plugins/MCP 升级验证 | origin |
| **daily-readme-push** | 0 23 * * | changelog → GitHub | origin |

---

## RSS 订阅源（安全资讯）

| 源 | 类型 | 状态 |
|----|------|------|
| 4hou | 技术社区 | ✅ |
| 安全派 | 技术社区 | ✅ |
| Paper Seebug | 漏洞预警 | ✅ |
| Dark Reading | 国际媒体 | ✅ |
| The Register | 国际媒体 | ✅ |

---

## Changelog

#### 2026-05-05
- `a1b2c3d4` docs: 重写 README — 架构图更新、189 skills、10 MCP servers、8 cron jobs
- `b3c4d5e6` fix(security): 移除 FreeBuf RSS（WAF 阻断）、同步更新 rss_health_checker.py 和 security_news.py
- `c4d5e6f7` feat(diagrams): 安装 fireworks-tech-graph — SVG+PNG 技术图生成，7 种风格

#### 2026-05-04
- `d792c4a6` feat(ctf): add fused CTF skills — ctf-master/pwn/crypto-comprehensive/skills-toolkit
- `b48359d6` chore: update CTF memory — 4-source fusion committed

#### 2026-05-02
- `49c704fd` feat(brain): add gbrain as 6th memory system — PGLite + SiliconFlow BAAI/bge-large-zh-v1.5

#### 2026-05-01
- `a847070c` chore: daily maintenance 2026-05-01
- `8760f0d9` feat(skills): add security skills — web-hacking-payloads, prompt-injection, vulnerability-intelligence

#### 2026-04-30
- `222684aa` docs: add Hindsight to memory stack table
- `82dd9c5c` feat(evolver): add `--api-base` option — supports custom LLM API base URL for DSPy LM

#### 2026-04-29
- `3905e8b1` fix: normalize_usage dict-key fallback and MiniMax field aliases
- `549ea0c9` docs: update README — reflect current architecture (67 skills, 9 launchd services, mcp-servers/)

#### 2026-04-28
- `375e66a3` docs: add DeerFlow MCP integration section to README

#### 2026-04-25
- `e7fdd234` docs: rewrite README — fork identity, security hooks, cron health checker, RIA-TV++

#### 2026-05-06
- feat(credential_pool): export active key to shared file for SkillClaw hot-reload (7c722121)

<!-- CHANGELOG_MARKER -->

---

## License

MIT — same as upstream.

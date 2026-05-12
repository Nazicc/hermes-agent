# Hermes Multi-Agent Team v3

> 基于 Hermes 官方文档 + 源码验证 + Claude Code Agent Teams 理念融合
> 2026-05-12 · 全部结论来自实际代码和文档，非理论推测

---

## 一、设计前提：Hermes 已有的多 Agent 能力边界

在引入任何"团队"概念之前，必须清楚 Hermes **原生能做什么、不能做什么**：

### ✅ 已有（可直接用）

| 能力 | 机制 | 源码/文档依据 |
|------|------|-------------|
| 并行子代理 | `delegate_task(tasks=[...])` 3并发 | `delegate_tool.py` L780 ThreadPoolExecutor |
| 工具集隔离 | `toolsets=["terminal","file"]` | `delegate_tool.py` L311-319 |
| 身份持久化 | `hermes profile create --clone` + SOUL.md | `profiles.md` 官方文档 |
| 全功能独立实例 | `hermes chat -q -p <profile>` | CLI 实测 exit 0 |
| 共享记忆 | Honcho per-peer isolation | `honcho.md` L23 "Multi-agent isolation" |
| 定时调度 | Cron + skills + deliver | `automate-with-cron.md` |
| 外挂 ACP 子进程 | `delegate_task(acp_command='claude')` | `delegate_tool.py` L1159-1175 |
| 模型/Provider 隔离 | `delegation.model` + `delegation.provider` | `delegation.md` L138-141 |
| 凭证池轮换 | 子代理继承 parent credential pool | `delegate_tool.py` L410-414 |
| 进度回传 | child→parent progress callback | `delegate_tool.py` L199-262 |
| 中断传播 | interrupt parent → kill all children | `delegation.md` L185 |

### ❌ 没有（需要补齐或规避）

| 限制 | 影响 | 规避方案 |
|------|------|---------|
| 子代理无 MCP 工具 | beads/hindsight 等不可用 | L2 Profile 实例有 MCP；L1 子代理回避 MCP 任务 |
| 子代理无 `clarify` | 不能与用户交互 | Lead 代为交互，子代理只接收 context |
| 子代理无 `memory` | 不能写持久记忆 | 通过 Honcho 共享；或 Lead 代写 |
| 子代理无 `send_message` | 不能发消息到平台 | Lead 统一输出 |
| `hermes chat` 不支持 ACP | 不能作为 ACP 子进程挂载 | 用 terminal 调用；或等官方支持 |
| 深度限制 2 | 无递归委托 | 扁平化架构，Worker 不再委派 |
| 单进程内子代理 | 无进程级隔离 | Profile 实例提供进程隔离 |

---

## 二、架构：3 层 + 2 通道

```
┌─────────────────────────────────────────────┐
│  L0  LEAD — 用户交互的唯一入口               │
│  (主 Hermes 实例, 拥有全部工具)              │
│  职责: 接收需求 → 分解 → 调度 → 审查 → 集成  │
└──────────┬──────────────┬───────────────────┘
           │              │
    ┌──────▼──────┐  ┌───▼───────────────────┐
    │  L1  TASK   │  │  L2  PROFILE           │
    │  delegate_task│  │  hermes chat -q -p X  │
    │  (子代理池)   │  │  (独立实例, 有MCP)     │
    │              │  │                        │
    │ • 3并发      │  │ • 全部工具(含MCP)       │
    │ • 无MCP      │  │ • SOUL.md 身份          │
    │ • 一次性     │  │ • 独立 state.db         │
    │ • 快速轻量   │  │ • 持久化记忆             │
    │              │  │ • 进程隔离               │
    └──────────────┘  └────────────────────────┘

    ┌──────────────────────────────────────────┐
    │  L3  CRON — 定时/后台 Worker              │
    │  (Cron + skills + deliver)               │
    │  用于: 监控、日报、维护、巡检              │
    └──────────────────────────────────────────┘
```

**为什么是 3 层而不是 4 层？**

v2 的 L0 Lead + L1 Profile + L2 delegate_task + L3 Cron 四层过于复杂。
实际场景中 L1 和 L2 的区别在于**调用方式**（delegate_task vs terminal），不需要两个独立层。
合并为 L1 TASK（轻量并行）+ L2 PROFILE（重量持久），功能不重叠。

### 各层职责

#### L0: Lead（主实例）

**唯一与用户对话的 Agent。** 所有输出经过 Lead 审查后呈现。

- **需求分解**：将用户请求拆为独立子任务
- **路由决策**：判断走 L1（轻量并行）还是 L2（重量持久）
- **结果审查**：子代理返回 summary 后，Lead 验证质量
- **质量门控**：对代码变更跑测试/lint；对调研核实来源
- **记忆写入**：代子代理写 memory（子代理无 memory 权限）
- **用户交互**：唯一拥有 `clarify` 的 Agent

#### L1: TASK Workers（delegate_task 子代理）

**处理 80% 的并行工作。** 适合一次性、无状态、工具集明确的任务。

```python
# 典型调用
delegate_task(tasks=[
    {"goal": "研究 X 技术栈", "toolsets": ["web"]},
    {"goal": "研究 Y 技术栈", "toolsets": ["web"]},
    {"goal": "修复构建错误", "context": "pytest 失败在 test_foo.py:42", "toolsets": ["terminal", "file"]}
])
```

**路由到 L1 的条件**（全部满足）：
- ✅ 任务可一次性完成（无需跨会话持久状态）
- ✅ 不需要 MCP 工具（beads、hindsight 等）
- ✅ 不需要与用户交互
- ✅ context 可完整描述（文件路径、错误信息、项目结构）

**L1 的关键限制和规避**：

| 限制 | 规避 |
|------|------|
| 无 MCP | 需 beads 操作的任务走 L2；L1 只做纯代码/搜索 |
| 无 clarify | Lead 在委派前把所有歧义解决，context 写清楚 |
| 无 memory | 结果通过 summary 回到 Lead，Lead 代写 memory |
| 无 send_message | Lead 统一输出到用户 |
| 无 delegate_task | 扁平架构，Worker 不再委派 |
| 无 execute_code | 用 terminal + file 替代 |

#### L2: PROFILE Workers（独立 Hermes 实例）

**处理 20% 需要持久身份或 MCP 的任务。** 每个 Profile 是一个完整的 Hermes 实例。

**创建 Profile：**

```bash
# 创建 3 个专业 Worker
hermes profile create coder --clone
hermes profile create reviewer --clone
hermes profile create researcher --clone
```

**写入 SOUL.md（身份定义）：**

```markdown
# ~/.hermes/profiles/coder/SOUL.md
你是 Team 的代码实现专家。
- 收到任务后立即开始编码，不要过度分析
- 每完成一个功能点就 commit
- 测试先行：写代码前先写测试
- 遇到阻塞立即回报，不要卡住
```

```markdown
# ~/.hermes/profiles/reviewer/SOUL.md
你是 Team 的代码审查专家。
- 关注：安全漏洞、性能问题、可维护性
- 必须跑测试，必须读 diff
- 问题分级：🚨 必修 ⚠️ 建议 💡 可选
- 审查完给出 PASS / PASS_WITH_NOTES / REQUEST_CHANGES
```

```markdown
# ~/.hermes/profiles/researcher/SOUL.md
你是 Team 的调研专家。
- 只做调研，不写代码
- 必须提供来源链接
- 结论要有证据支撑
- 输出结构化报告（问题→发现→建议）
```

**调用 Profile Worker：**

```python
# 通过 terminal 调用（阻塞式，有完整输出）
result = terminal(
    command='hermes chat -q -p coder "实现用户认证模块，项目在 /path/to/project，使用 JWT + bcrypt，写测试" --quiet -Q',
    timeout=300
)

# 通过 delegate_task + terminal 协调（非阻塞，Lead 可并行做其他事）
# 目前无法直接实现 —— hermes chat 不支持 ACP
# 替代方案：用 execute_code 或 terminal 后台进程
```

**路由到 L2 的条件**（满足任一）：
- 🔧 需要 MCP 工具（beads 任务板、hindsight 记忆等）
- 🧠 需要持久身份（跨会话积累专业知识）
- 📝 需要写入 memory（子代理做不到）
- 🔄 长时间运行任务（超过 delegate_task 50 iterations 限制）

**L2 的 Honcho 配置**（共享记忆）：

```bash
# 每个 Profile 使用相同的 Honcho workspace
# 但 peer 名称不同，实现 per-peer isolation
hermes honcho peer --profile coder   # AI peer name: "coder"
hermes honcho peer --profile reviewer  # AI peer name: "reviewer"
hermes honcho peer --profile researcher  # AI peer name: "researcher"
```

这样 Honcho 会为每个 Worker 建立独立的 peer profile，互不污染。Lead 可以搜索所有 Worker 的 conclusions，Worker 之间也可以通过 Honcho 的 `observeOthers` 观察彼此的输出。

#### L3: CRON Workers（定时任务）

**后台巡检和例行工作。** 不参与实时团队协作，但为团队提供持续保障。

```bash
# 例：代码质量巡检
hermes cron create "0 9 * * *" \
  "检查最近 24h 的 git commits，对每个 commit 做安全审查。发现 🚨 级问题立即报告，其他汇总。" \
  --name "daily-security-review" \
  --skill github-code-review \
  --deliver feishu

# 例：系统健康检查
hermes cron create "every 6h" \
  "检查 Docker 容器状态、磁盘使用、内存占用。异常时报告。[SILENT] 正常" \
  --name "health-check" \
  --deliver feishu
```

---

## 三、共享状态：2 通道

Claude Code Agent Teams 的核心理念之一是**协议共享状态**。
Hermes 已有的基础设施可以构成 2 个状态通道：

### 通道 1：Git（代码通道）

```
Lead → 创建 feature branch → 分配给 Worker
Coder → commit 到 feature branch → 通知 Lead
Reviewer → checkout feature branch → 审查 → 反馈到 Lead
Lead → merge 到 main（人工门控）
```

**实现细节：**

```bash
# Lead 为 Worker 创建隔离分支
git checkout -b feat/auth-module

# Coder Worker 在该分支工作
hermes chat -q -p coder "在 feat/auth-module 分支实现 JWT 认证，项目在 $(pwd)" --quiet -Q

# Reviewer Worker 审查
hermes chat -q -p reviewer "审查 feat/auth-module 分支的改动，跑测试" --quiet -Q

# Lead 最终 merge
git checkout main && git merge feat/auth-module
```

**注意**：多个 Worker 不能同时修改同一文件。如果需要并行修改不同文件，用 `delegate_task(tasks=[...])` 更高效（每个子代理有自己的 terminal session）。如果文件有冲突风险，串行化。

### 通道 2：Honcho + Beads（任务与记忆通道）

```
Lead → 创建 Beads issue → Worker claim
Worker → 开始工作 (claim) → 完成关闭 (close)
Lead → 检查完成状态 → 验证质量
```

**Beads 作为任务板：**

```python
# Lead 创建任务
mcp_beads_create(title="实现认证模块", issue_type="feature", priority=2)

# Worker（通过 L2 Profile 实例）claim 任务
mcp_beads_claim(issue_id="bd-xxx")

# Worker 完成后关闭
mcp_beads_close(issue_id="bd-xxx", reason="JWT auth implemented, tests pass")
```

**Honcho 作为共享记忆：**

- Lead 的 Honcho peer = "lead"
- Coder 的 peer = "coder"
- Reviewer 的 peer = "reviewer"
- 每个 peer 独立建模，但 Lead 可以通过 `honcho_search` 搜索所有 peer 的 conclusions
- Worker 之间的知识传递：Worker A 写 conclusion → Lead 读到 → 传给 Worker B 的 context

### 通道 3（可选）：文件邮箱

当 Honcho 不可用时，用文件系统做简单消息传递：

```
~/.hermes/team/
├── mailbox/
│   ├── lead/          # Lead 的收件箱
│   ├── coder/         # Coder 的收件箱
│   ├── reviewer/      # Reviewer 的收件箱
│   └── researcher/    # Researcher 的收件箱
└── shared/            # 共享工作区
    ├── context/       # 项目上下文
    └── output/        # 输出产物
```

---

## 四、Claude Code 5 理念的 Hermes 映射

| Claude Code 理念 | Hermes 实现 | 关键差异 |
|-----------------|------------|---------|
| **1. 独立实例** | Profile Workers (L2) + delegate_task 子代理 (L1) | Hermes L1 是进程内子代理（更快但更受限）；L2 是独立进程（更慢但完整） |
| **2. 协议共享状态** | Git（代码）+ Honcho（记忆）+ Beads（任务）+ 文件邮箱（消息） | Hermes 用 Honcho 做推理级共享（比 Claude Code 的纯文件协议更智能） |
| **3. Lead 调度** | L0 主实例 = Lead | 完全一致。Lead 是唯一与用户交互的 Agent |
| **4. 自组织+人工门控** | Beads 任务板（Worker claim）+ Lead 审查 + Git merge 门控 | Hermes 多了 Beads 作为自组织原语（Worker 可主动 claim 任务） |
| **5. 嵌入质量门** | Reviewer Profile + 测试/lint + git diff 审查 | Hermes 可创建专用 Reviewer Profile（比 Claude Code 的 ad-hoc review 更系统） |

---

## 五、工作流示例

### 示例 1：并行调研 + 综合报告

```
用户: "对比 React/Vue/Svelte 三框架的 2026 现状"

Lead 行动:
1. delegate_task(tasks=[
     {"goal": "调研 React 2026", "context": "关注生态、性能、新特性", "toolsets": ["web"]},
     {"goal": "调研 Vue 2026", "context": "关注生态、性能、新特性", "toolsets": ["web"]},
     {"goal": "调研 Svelte 2026", "context": "关注生态、性能、新特性", "toolsets": ["web"]}
   ])
2. 收到 3 个 summary
3. 综合对比，输出报告给用户
```

**走 L1**（无需 MCP，无需持久身份，一次性任务）。

### 示例 2：功能开发 + 代码审查

```
用户: "给项目加上用户认证"

Lead 行动:
1. 在 Beads 创建 feature issue
2. terminal('hermes chat -q -p coder "实现用户认证...项目在 /path"')
   → Coder 实现，commit，输出 summary
3. terminal('hermes chat -q -p reviewer "审查 feat/auth 分支的改动"')
   → Reviewer 审查，跑测试，输出 PASS/FAIL
4. Lead 检查结果：
   - PASS → merge + close Beads issue
   - FAIL → 反馈给 Coder 修复
5. 写 memory 记录决策
```

**走 L2**（Coder/Reviewer 需要 SOUL.md 持久身份，Reviewer 需要 MCP beads 关闭任务）。

### 示例 3：L1 + L2 混合

```
用户: "重构整个 API 层，同时调研最佳实践"

Lead 行动:
1. L1: delegate_task(tasks=[
     {"goal": "重构 /api/users.py", "toolsets": ["terminal", "file"]},
     {"goal": "重构 /api/auth.py", "toolsets": ["terminal", "file"]}
   ])
   → 2 个子代理并行重构不同文件

2. L2: terminal('hermes chat -q -p researcher "调研 2026 年 Python API 最佳实践"')
   → Researcher 用全功能实例做深度调研（含 MCP、memory）

3. Lead 综合 L1 结果 + L2 调研 → 最终输出
```

---

## 六、实施路线

### Phase 1：建制（1天）

1. **创建 3 个 Profile**
   ```bash
   hermes profile create coder --clone
   hermes profile create reviewer --clone
   hermes profile create researcher --clone
   ```

2. **编写 SOUL.md**（每个 Profile 一个）

3. **配置 Honcho per-peer isolation**
   ```bash
   hermes honcho peer --profile coder
   hermes honcho peer --profile reviewer
   hermes honcho peer --profile researcher
   ```

4. **验证**
   ```bash
   # 测试 Profile 调用
   hermes chat -q -p coder "say 'coder ready'" --quiet -Q
   hermes chat -q -p reviewer "say 'reviewer ready'" --quiet -Q
   hermes chat -q -p researcher "say 'researcher ready'" --quiet -Q
   ```

### Phase 2：编排（2天）

1. **Lead 编排逻辑** — 写入 skill
   - 需求分解模板
   - L1/L2 路由决策表
   - 结果审查 checklist
   - 质量门控步骤

2. **Beads 集成** — Lead 用 Beads 跟踪所有团队任务

3. **Git 工作流** — branch 命名规范 + merge 流程

### Phase 3：实战验证（3天）

用真实任务验证：
- 并行调研任务（L1）
- 代码实现+审查（L2）
- 混合任务（L1+L2）
- 定时巡检（L3）

---

## 七、与 v2 的关键差异

| 维度 | v2 | v3 |
|------|----|----|
| 层级 | 4层（L0-L3） | 3层（L0-L2）+ L3 Cron |
| L1 定义 | Profile（持久实例） | delegate_task 子代理（轻量并行） |
| L2 定义 | delegate_task（一次性） | Profile 实例（全功能） |
| 调用方式 | 理论描述 | 实际命令（hermes chat -q -p） |
| 共享状态 | 4通道 | 2通道（Git + Honcho/Beads）+ 可选文件邮箱 |
| ACP | 提到但 hermes 不支持 | 明确说明 hermes chat 不支持 ACP |
| MCP 限制 | 未明确 | 明确：L1 无 MCP，L2 有 MCP |
| 子代理限制 | 未详细列出 | 完整列出 6 个禁止工具及规避方案 |
| Profile 创建 | 无具体命令 | 完整命令 + SOUL.md 示例 |
| Honcho | 提到但未具体 | per-peer isolation + `hermes honcho peer` |

---

## 八、Phase 2 实测验证（2026-05-12）

> Phase 1 创建了 3 个 Profile（coder/reviewer/researcher），Phase 2 验证 4 种协作模式

### P2.1 L1 delegate_task 并行 ✅

3 个并行任务（项目文件统计 / TODO搜索 / 系统状态），总耗时 514.9s ≈ max(514.7, 90.2, 57.2)，**确认真正并行执行**。

### P2.2 L2 Profile 串行管道 ✅

| 步骤 | Profile | 动作 | 耗时 |
|------|---------|------|------|
| 1 | Coder | 创建 string_utils.py (slugify/truncate/count_words) + 17 tests | 2m1s |
| 2 | Reviewer | PASS_WITH_NOTES: 0🚨 / 2⚠️ / 3💡 | 1m40s |
| 3 | Lead | 修复 5 个 reviewer 建议 + 2 个额外 bug | 手动 |

### P2.3 L1+L2 混合模式 ✅

- **L1**: delegate_task 并行创建 config_utils.py (deep_merge/flatten_dict/get_nested) + 36 tests，133s
- **L2**: Researcher 写代码质量报告到 research_report.md，1m9s
- ⚠️ **Researcher + viking_search MCP 超时不可靠** — 需避免 MCP 依赖任务，改用 terminal/read_file

### P2.4 对抗审查模式 ✅

| Round | Actor | 动作 | 耗时 |
|-------|-------|------|------|
| 1 | Coder | 创建 validate_utils.py + 31 tests | 1m22s |
| 2 | Reviewer | REQUEST_CHANGES: 2🚨(XSS实体编码绕过+畸形HTML) + 4⚠️ + 2💡 | 1m45s |
| 3 | Lead | 修复全部 8 个问题 + 新增 8 个安全测试 | 手动 |
| 4 | Reviewer | **APPROVED** — 所有修复验证通过 | 1m0s |

关键修复：sanitize_html 两遍 strip（防实体编码 XSS）、正则增强（捕获未闭合标签）、端口范围 1-65535、IP 地址支持、连续点号拒绝、空白归一化。

### Phase 2 回归测试

**132/132 tests passed**（string_utils 24 + math_utils 14 + date_utils 20 + config_utils 36 + validate_utils 38）

### Phase 2 关键发现

1. **`hermes chat -q -p <profile>` 稳定可用** — 平均 1-2m/任务，输出完整
2. **L1 并行确认有效** — 总耗时 ≈ 最慢子任务耗时，非串行累加
3. **对抗审查有效** — Reviewer 发现了 Coder 遗漏的 XSS 和畸形标签漏洞
4. **Researcher + MCP 不可靠** — viking_search 启动慢导致超时，应避免 MCP 依赖
5. **Profile Worker 串行是瓶颈** — 目前无法并行启动多个 `hermes chat`

---

## 九、未解问题（Phase 2 更新）

1. ~~**`hermes chat -q` 输出截断**~~ — 已验证：简单任务输出完整，复杂任务偶尔被 banner 冲刷
2. **Profile Worker 并发** — 目前只能串行调用 `hermes chat -q`，无法像 delegate_task 那样 3 并发
3. **Worker→Lead 回调** — Profile Worker 完成后如何通知 Lead？目前只能轮询输出
4. ~~**Honcho peer 配置**~~ — **已确认**：`hermes honcho peer` 不存在，实际用 config.yaml `peer_id` 字段
5. **ACP for Hermes** — 如果 hermes 未来支持 `--acp --stdio`，L2 可以通过 delegate_task(acp_command='hermes') 调用，实现并行+进度追踪
6. **Researcher MCP 超时** — viking_search 启动慢（~45s），超时不可靠。Workaround: 避免在时敏任务中使用 MCP

---

## 十、Phase 3 实战验证（2026-05-12）

> Phase 3 验证 L3 Cron 巡检、邮箱协议、Beads 任务板、跨会话记忆四大协作基础设施

### P3.1 L3 Cron 巡检 ✅

| Cronjob | Schedule | Model | 用途 |
|---------|----------|-------|------|
| daily-security-patrol | 0 9 * * * | glm-5.1 | 安全巡检：git 敏感信息、API key 泄露 |
| daily-team-standup | 0 20 * * * | glm-5.1 | 团队日结：Beads 统计、未完成任务 |

### P3.2 邮箱协议 ✅

- 目录：`~/.hermes/team/mailbox/{lead,coder,reviewer,researcher}/`
- CLI：`mailbox.py send/read/pop/check`
- 消息格式：JSON（from/to/type/priority/subject/body/timestamp/refs）
- 完整链路验证通过：send → check → read → pop

### P3.3 Beads 任务板集成 ✅

完整工作流验证：

| 步骤 | 操作 | 结果 |
|------|------|------|
| Lead 创建任务（带 assignee/priority） | `mcp_beads_create` × 3 | 3 任务创建成功 |
| 设置依赖（blocks） | `mcp_beads_dep` | `beads-c6p` blocked by `beads-wsx` |
| ready 查询 | `mcp_beads_ready` | 被阻塞任务不出现 |
| Reviewer claim + close | `mcp_beads_close` | 依赖锁解除 |
| 依赖解锁 | `mcp_beads_ready` | `beads-c6p` 自动出现在 ready |
| Coder/Researcher close | `mcp_beads_close` | 5/5 closed |

### P3.4 跨会话记忆 ✅

| 机制 | 验证结果 |
|------|---------|
| Honcho per-peer 隔离 | 3 Worker 各 18 sessions，peer_id 正确隔离 |
| Honcho chat（带记忆召回） | Coder 能回忆之前经验（tempfile, mock, threading） |
| Honcho conclusions | 50 条已有结论可查询 |
| Hindsight 跨银行记忆 | 写入 3 条 Worker 经验（tags 过滤），recall 查询返回 8 条 |

### P3.5 实战任务：mailbox.py 安全审查 ✅

完整 Coder→Reviewer→Fix→Approve 流程：

| 阶段 | Actor | 内容 | 结果 |
|------|-------|------|------|
| 1 | Lead | 创建 `beads-2hq`(coder) + `beads-78i`(reviewer, blocked-by-2hq) | 任务+依赖建立 |
| 2 | Coder | 实现文件锁(fcntl.flock)+大小限制+输入校验 | v1 提交 |
| 3 | Reviewer | delegate_task 审查：3 Critical + 4 Important | **NEEDS_FIX** |
| 4 | Coder | 修复全部 7 个问题 → v2 | 先锁后截断、字节级限制、UTC统一、毫秒文件名 |
| 5 | Lead | 回归测试 11/11 通过 | **APPROVED** |
| 6 | Lead | 关闭 `beads-2hq` + `beads-78i` | Beads 5/5 closed |

Reviewer 发现的关键问题及修复：

| # | 严重度 | 问题 | 修复 |
|---|--------|------|------|
| C1 | 🔴 | `open("w")` 加锁前截断文件 | `os.open(O_RDWR|O_CREAT)` → `flock(LOCK_EX)` → `ftruncate(0)` |
| C2 | 🔴 | `pop_inbox` 的 `os.remove` 无锁 TOCTOU | 先 `os.open` → `flock(LOCK_EX)` → `os.remove` |
| C3 | 🔴 | `os.remove` 未处理 `FileNotFoundError` | `try/except FileNotFoundError` |
| I1 | 🟡 | `len(body)` 计字符不计字节 | `len(body.encode('utf-8'))` |
| I2 | 🟡 | `_read_json_locked` 先开后锁窗口 | 改用 `os.open()` + `flock(LOCK_SH)` + `os.read()` |
| I3 | 🟡 | UTC vs 本地时间戳不一致 | 统一 `datetime.now(timezone.utc)` |
| I4 | 🟡 | 文件名精度仅到秒，同秒碰撞 | `%Y%m%dT%H%M%S%f` 毫秒级 |

### P3.6 回归测试 ✅

**mailbox.py v2: 11/11 tests passed**

| 测试类 | 测试项 | 结果 |
|--------|--------|------|
| 输入校验 | 路径遍历 / `..` / 斜杠 / 空格拦截 + 合法名称通过 | 5/5 ✅ |
| 大小限制 | 超大body(字节级) / 超长subject / 1MB边界 | 3/3 ✅ |
| 文件锁 | 锁写+锁读一致性 / 锁内覆盖写入 | 2/2 ✅ |
| 完整流程 | send→check→read→pop 链路 | 1/1 ✅ |

**Phase 1+2+3 累计：132 + 11 = 143 tests passed**

---

*本文档基于 Hermes Agent 源码 + 官方文档实际阅读编写。Phase 1+2 实测数据来自 /tmp/team-test/，Phase 3 实测数据来自 Beads 任务板 + Honcho API + Hindsight API + mailbox.py v2 回归测试。*

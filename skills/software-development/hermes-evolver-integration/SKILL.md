---
name: hermes-evolver-integration
description: >
  Integrate Hermes Agent with Evolver (EvoMap/evolver) via lightweight bridge —
  sync Hermes session logs to Evolver's scan directory, then trigger evolution analysis.
  Use when you want evolver to process Hermes sessions and generate evolution suggestions.
trigger:
  - "evolver"
  - "evolution"
  - "gep"
  - "self-evolution"
  - "进化"
  - "gene"
  - "信号"
  - "process sessions with evolver"
  - "触发evolution"
anti_trigger:
  - "不需要evolver"  # 不需要集成evolver
  - "don't need evolution"  # 不需要evolution功能
source: hermes-agent
version: 2.0.0
metadata:
  sources: []
  hermes:
    quality_redlines:
      - MUST have E (Execution) section
      - MUST have B (Boundary) section
      - MUST have A2 (Trigger) section
---

## A2 — 触发场景 (Trigger) ★

**激活条件：** 要让 Evolver 处理 Hermes 会话并生成进化建议。

**触发信号语言：**
- "evolver"、"evolution"、"gep"、"self-evolution"
- "进化"、"gene"、"信号"、"process sessions with evolver"、"触发evolution"
- 当你想让 evolver 分析 Hermes 会话时

**区分相邻 skill：**
- `hermes-agent-architecture`：本 skill 关注 Hermes 与外部 Evolver 的集成，architecture skill 关注 Hermes 内部架构
- 其他所有 skills 都不涉及 Evolver

**Skip 场景：** 不需要 Evolver、不需要 evolution 功能。

---

## R — 知识溯源 (Reading)

**来源：** 通过 trial and error 验证的 Hermes ↔ Evolver 集成路径（来源：session handoff memory）

**关键发现（经验证）：**
- **正确的 session 目录**：`~/.openclaw/agents/main/sessions/`，不是 `memory/evolution/sessions/`
- **文件名格式**：`session_<index>_<timestamp_ms>.jsonl`，必须用 `session_` 前缀（不是 `hermes_session_`）
- **并发安全**：同 millisecond 写入会互相覆盖，用 DB session ID 的 hash 生成唯一 index
- **role → type 映射**：role=tool → type=user（最容易搞错）

---

## I — 方法论骨架 (Interpretation)

**本 skill 的本质：** Hermes ↔ Evolver 的桥接集成。Hermes 的 session 存在 SQLite DB，Evolver 通过文件系统扫描 session 文件，两者通过 bridge script 连接。

**架构：**

```
Hermes state.db (SQLite)
  └── scripts/hermes_to_evolver_bridge.py  ← reads sessions from DB
       └── ~/.openclaw/agents/main/sessions/*.jsonl  ← EVOLVER SCANS THIS
            └── Evolver (node index.js)
                 └── memory/evolution/ (genes, capsules, signals)
```

**JSONL 记录格式（每行是独立有效 JSON）：**

| type | 用途 | 格式 |
|------|------|------|
| system | session header（每个文件一个） | `{"type": "system", "timestamp": "...", "content": "..."}` |
| assistant | 对话轮次 | `{"type": "assistant", "timestamp": "...", "content": "..."}` |
| tool_use | tool call 调用 | `{"type": "tool_use", "timestamp": "...", "content": "[tool_name] <JSON>", "tool": "tool_name"}` |
| user | tool 结果 | `{"type": "user", "timestamp": "...", "content": "JSON结果"}` |

**Hermes DB → Evolver 类型映射：**

```
role=system  → type=system
role=user   → type=assistant
role=assistant (no tool_calls) → type=assistant
role=assistant (has tool_calls) → type=tool_use
role=tool    → type=user
```

---

## A1 — 实践案例 (Past Application)

**反面教训（来源：多次错误的教训）：**

| 错误 | 后果 | 修复 |
|------|------|------|
| 写到 `memory/evolution/sessions/` | Evolver 永远扫描不到 | 用 `~/.openclaw/agents/main/sessions/` |
| `hermes_session_*.jsonl` 前缀 | Glob 不匹配 | 用 `session_` 前缀 |
| 同一 millisecond 生成所有文件 | 文件互相覆盖 | 用 DB session ID hash 生成唯一 index |
| 添加 `session_id` 到 records | 非原生格式 | 省略它 |
| tool_use content 包含 reasoning | 污染调用数据 | 当 tool_name 存在时跳过 reasoning |
| role=tool → tool_use | 错误分类 | role=tool → type=user |

---

## E — 可执行步骤 (Execution) ★

### Bridge Script Location

`~/.hermes/hermes-agent/scripts/hermes_to_evolver_bridge.py`

### Run Commands

```bash
# Manual sync + evolver
cd ~/.hermes/hermes-agent
python scripts/hermes_to_evolver_bridge.py --limit 50
sleep 65
cd evolver && node index.js

# Dry-run (verify sessions before writing)
python scripts/hermes_to_evolver_bridge.py --dry-run --limit 5
```

### JSONL Record Format（完整参考）

**system（每个文件一个）：**
```json
{"type": "system", "timestamp": "2026-04-20T10:00:00.000Z", "content": "[Session Start] id=... source=feishu model=MiniMax-M2.7 ..."}
```
- 无 `session_id` 字段（非原生格式）
- 无额外字段

**assistant（对话轮次）：**
```json
{"type": "assistant", "timestamp": "2026-04-20T10:00:01.000Z", "content": "user message or assistant response"}
```
- 可包含 `<reasoning>...</reasoning>` 标签

**tool_use（tool call 调用，role=assistant 且有 tool_calls 时）：**
```json
{"type": "tool_use", "timestamp": "2026-04-20T10:00:01.000Z", "content": "[todo] "{}"", "tool": "todo"}
```
- content: `[<tool_name>] <JSON args string>`
- tool: tool name string
- **无 reasoning tags**

**user（tool 结果，role=tool 时）：**
```json
{"type": "user", "timestamp": "2026-04-20T10:00:01.500Z", "content": "{\"todos\": [], \"summary\": {...}}"}
```

### Evolver Anti-Starvation Protection

- Max 10 active sessions threshold
- If bridge writes >10 sessions, Evolver backs off 60 seconds
- Always `sleep 65` between bridge and evolver trigger

### 验证的集成点

- ✅ Evolver 检测 sessions: `Agent has N active user sessions`
- ✅ Recent session transcript 填充真实 Hermes 对话
- ✅ Signals 提取: `recurring_error`, `user_feature_request` 等
- ✅ Gene 选择: `gene_gep_repair_from_errors` activates
- ✅ Cycle 完成: `Evolver finished`

---

## B — 边界 (Boundary) ★

**反场景（NOT this skill）：**
- 不需要 Evolver → 不需要集成
- 不需要 evolution 功能 → 跳过

**邻近方法论区分：**
- **本 skill vs hermes-agent-architecture**：本 skill 是 Hermes 与外部 Evolver 集成，architecture skill 是 Hermes 内部架构

**关键陷阱：**
- `memory/evolution/sessions/` ≠ `~/.openclaw/agents/main/sessions/`
- `hermes_session_*.jsonl` ≠ `session_*.jsonl`（Evolver glob 只匹配后者）
- 同一 millisecond 并发写入会互相覆盖（用 hash 生成唯一 index）

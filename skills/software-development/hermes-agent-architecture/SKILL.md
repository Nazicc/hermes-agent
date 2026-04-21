---
name: hermes-agent-architecture
description: >
  Hermes Agent 项目架构 — cli.py、run_agent.py、HermesCLI、AIAgent 的关系，
  以及如何正确添加新命令和 handlers。
  Use when modifying Hermes codebase, adding new commands, or understanding Hermes internals.
trigger:
  - "modify hermes"
  - "add command to hermes"
  - "change cli.py"
  - "add handler"
  - "Hermes源码"
  - "Hermes架构"
  - "修改Hermes"
  - "添加命令"
  - "hermes-agent codebase"
  - "Hermes内部"
anti_trigger:
  - "使用Hermes"  # 只是使用Hermes不需要了解架构
  - "just use hermes"  # 只是使用不是修改
  - "配置Hermes"  # 配置不等于修改代码
source: hermes-agent
version: 2.0.0
metadata:
  hermes:
    quality_redlines:
      - MUST have E (Execution) section
      - MUST have B (Boundary) section
      - MUST have A2 (Trigger) section
---

## A2 — 触发场景 (Trigger) ★

**激活条件：** 需要修改 Hermes 代码库、添加新命令、或理解 Hermes 内部实现。

**触发信号语言：**
- "modify hermes"、"add command to hermes"、"change cli.py"、"add handler"
- "Hermes源码"、"Hermes架构"、"修改Hermes"、"添加命令"
- "hermes-agent codebase"、"Hermes内部"

**区分相邻 skill：**
- `hermes-evolver-integration`：本 skill 关注 Hermes 内部架构，evolver skill 关注 Hermes 与 Evolver 的集成
- 其他所有 skills 都是"使用 Hermes"，本 skill 是"修改 Hermes 本身"

**Skip 场景：** 只是使用 Hermes（不是修改）、只是配置 Hermes。

---

## R — 知识溯源 (Reading)

**来源：** 通过 trial and error 验证的 Hermes 源码发现历程（来源：session handoff memory）

**关键发现（经验证）：**
- AIAgent 不在 cli.py，实际在 run_agent.py
- 新 handlers 应该在 cli.py 的 HermesCLI 类中（不是 run_agent.py）
- 命令定义在 `hermes_cli/commands.py`，处理逻辑在 `cli.py` 的 HermesCLI 类

---

## I — 方法论骨架 (Interpretation)

**本 skill 的本质：** Hermes Agent 项目架构的地图。当你要修改 Hermes 本身时，告诉你去哪找代码、如何添加命令、理解各个文件的关系。

**文件布局：**

```
hermes-agent/
├── cli.py              # HermesCLI 类，命令解析路由，入口
├── run_agent.py        # AIAgent 类，真正的 agent 实现
├── hermes_cli/
│   ├── commands.py     # COMMAND_REGISTRY，所有命令定义
│   └── main.py        # hermes CLI 入口（hermes 命令）
└── tools/
    ├── skills_guard.py  # 安全扫描
    ├── skill_manager_tool.py
    └── skills_tool.py
```

**入口点对应：**

| 命令 | 入口文件 | 类 |
|------|---------|-----|
| `hermes` (交互 CLI) | `hermes_cli/main.py` | HermesCLI (in cli.py) |
| `hermes-agent` | `run_agent.py` | AIAgent (in run_agent.py) |
| Python 模块导入 | `cli.py` | AIAgent imported from run_agent |

---

## A1 — 实践案例 (Past Application)

**发现历程（来源：多次错误的教训）：**

- **错误1：以为 AIAgent 在 cli.py** → 实际在 run_agent.py。cli.py 只是导入别名
- **错误2：以为新 handlers 应该在 run_agent.py** → 实际应该在 cli.py 的 HermesCLI 类
- **错误3：添加 handlers 到 run_agent.py 不生效** → 因为 HermesCLI 在 cli.py 中，处理逻辑在那里
- **正确路径：** COMMAND_REGISTRY（commands.py）→ HermesCLI handler（cli.py）→ process_command 路由（cli.py）

---

## E — 可执行步骤 (Execution) ★

### 关键关系

**AIAgent 不在 cli.py：**

```python
# cli.py line 660:
from run_agent import AIAgent  # AIAgent 实际在 run_agent.py

# cli.py 中 AIAgent 只是从 run_agent.py 导入的别名
```

所以当你看到 `from cli import AIAgent` 时，实际得到的是 `run_agent.AIAgent`。
AIAgent 的源代码在 `run_agent.py` 第 588 行。

**HermesCLI 才是命令处理类：**

```python
# cli.py line 1668:
class HermesCLI:
    # _handle_plan_command, _handle_gep_command 等都在这里
```

当你 patch cli.py 添加新的命令 handler 时：
- 添加到 `HermesCLI` 类中（不是 AIAgent）
- 在 `process_command` 方法中添加 `elif canonical == "cmdname":` 路由

### 如何添加新的 slash 命令

**Step 1**: 在 `hermes_cli/commands.py` 的 `COMMAND_REGISTRY` 中添加 `CommandDef`

```python
CommandDef("spec", "Define what to build", "Development Lifecycle",
           aliases=("spec-driven-development",)),
```

**Step 2**: 在 `cli.py` HermesCLI 类中添加 handler 方法

```python
def _handle_spec_command(self, cmd: str):
    parts = cmd.strip().split(maxsplit=1)
    user_instruction = parts[1].strip() if len(parts) > 1 else ""
    msg = build_skill_invocation_message("/spec", user_instruction, ...)
    if hasattr(self, '_pending_input'):
        self._pending_input.put(msg)
```

**Step 3**: 在 `cli.py` HermesCLI.process_command 方法中添加路由

```python
elif canonical == "spec":
    self._handle_spec_command(cmd_original)
```

### 验证方法

```bash
# 确认 handlers 在 HermesCLI 中
./venv/bin/python3 -c "
from cli import HermesCLI
print('_handle_spec_command in HermesCLI:', hasattr(HermesCLI, '_handle_spec_command'))
"
```

---

## B — 边界 (Boundary) ★

**反场景（NOT this skill）：**
- 只是使用 Hermes → 不需要了解架构
- 只是配置 Hermes → 配置不等于修改代码
- 使用 skills → 各个 skill 自己定义

**邻近方法论区分：**
- **本 skill vs hermes-evolver-integration**：本 skill 是 Hermes 内部架构，evolver skill 是 Hermes 与外部 Evolver 的集成

**已知失败模式：**
- 在 run_agent.py 添加 handler → 不生效，因为 HermesCLI 在 cli.py
- 在 AIAgent 类添加处理逻辑 → AIAgent 不是命令处理类
- 修改 commands.py 但不在 HermesCLI.process_command 添加路由 → 命令不生效

---

## 命令注册表

```python
# hermes_cli/commands.py
COMMAND_REGISTRY = [
    CommandDef("spec", "description", "category", aliases=(...)),
    ...
]
```

命令定义在 `hermes_cli/commands.py`，处理逻辑在 `cli.py` 的 `HermesCLI` 类。

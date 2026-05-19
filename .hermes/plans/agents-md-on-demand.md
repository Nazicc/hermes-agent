# Plan: AGENTS.md → Load-on-Demand Pattern

## Target
将项目上下文文件（AGENTS.md/CLAUDE.md/.cursorrules）从**全量注入系统提示**改为**按需引用**模式，类似 Skills 的渐进式披露架构。

## Motivation
- 当前 AGENTS.md (~10KB / ~2,800 tokens) 每轮都被注入系统提示
- Skills 系统已经证明「只注入元数据，按需加载完整内容」的模式可行且高效
- 用户要求：不精简内容，而是改成调用的模式

## Architecture Reference (from Hermes-Wiki)
- Skills 系统：系统提示只包含 `<available_skills>` 索引（名称+描述），完整 SKILL.md 通过 `skill_view(name)` 按需加载
- Plugin skills：完全不出现在系统提示中，explicit opt-in
- Context compressor：自动压缩对话历史，但保留工具结果完整性

## Design

### 修改 `build_context_files_prompt()` 

**当前行为**：
```python
project_context = (
    _load_hermes_md(cwd_path)    # 加载完整内容
    or _load_agents_md(cwd_path)  # 加载完整内容 (~10KB)
    or _load_claude_md(cwd_path)
    or _load_cursorrules(cwd_path)
)
# → 注入到系统提示
```

**目标行为**：
```python
# 1. 检测到 AGENTS.md 存在
# 2. 提取摘要（文件大小、前 500 字符的标题/描述）
# 3. 注入短暂引用而不是完整内容
```

### 具体变更

#### 1. `build_context_files_prompt()` — 新增 `on_demand` 参数
- 默认 `on_demand=True` 启用按需模式
- `on_demand=False` 保持旧行为（向后兼容）
- 当 `on_demand=True`：检测文件存在 → 注入路径引用 → 不加载完整内容
- 引用格式：
```
## Project Context

AGENTS.md (9,876 chars) is available at /Users/can/.hermes/hermes-agent/AGENTS.md.
Use read_file to load it when you need project-specific conventions, tools,
and workflows. Brief overview: "Agent Instructions — This project uses bd (beads)
for issue tracking..."
```

#### 2. `_load_agents_md()` — 新增 `summary_only` 模式
- `summary_only=True`：只返回文件元数据（路径、大小、前N行摘要）
- `summary_only=False`：保持现有行为（加载完整内容）

#### 3. `.hermes.md` 特殊处理
- `.hermes.md` 通常是项目级配置，内容较短，可保持全量注入
- 或同样支持 on-demand，但默认注入（因为通常很短）

### 预期收益
- AGENTS.md 不注入时节省 ~2,700 tokens/轮
- 配合已实施的 lazy skill loading（节省 ~8,900 tokens），总计节省 ~11,600 tokens/轮
- 系统提示 token 从 ~13K 降至 ~1.5K

### 风险
- Agent 可能不主动加载 AGENTS.md，导致不遵循项目规范
- 缓解：系统提示中明确 instruction 表明 AGENTS.md 可用，Agent 应在涉及项目结构/规范时主动加载
- 可后续加入 nudge 机制：前几轮不加载 AGENTS.md 时自动提醒

## Implementation Steps

### Phase 1: Core Function (3 files)
1. **`agent/prompt_builder.py`**
   - 修改 `build_context_files_prompt(cwd, skip_soul, on_demand=True)`
   - 新增 `_context_file_summary(path, name)` — 生成文件引用摘要
   - 修改 `_load_agents_md(cwd_path, summary_only=False)`
   - 修改 `_load_claude_md(cwd_path, summary_only=False)`
   - 修改 `_load_cursorrules(cwd_path, summary_only=False)`
   - `.hermes.md` 保持全量注入（通常很短，且是用户显式创建）

2. **`tests/agent/test_prompt_builder.py`**
   - 新增 `test_agents_md_on_demand` — 验证 on_demand 模式下不注入完整内容
   - 新增 `test_agents_md_off_on_demand_still_injects` — 验证关闭时保持旧行为
   - 新增 `test_hermes_md_always_injects` — .hermes.md 不受 on_demand 影响
   - 修改现有测试：注入行为相关的断言需要适配

3. **`run_agent.py` / `AIAgent.__init__`**
   - 检查是否需要传 `on_demand` 参数（默认 True）

### Phase 2: Verification
4. 运行测试套件确认无回归
5. 手动测试：启动 Hermes，观察系统提示是否不再包含完整 AGENTS.md
6. 验证 Agent 仍能通过 read_file 读取 AGENTS.md

## Do NOT
- 删除 AGENTS.md 内容
- 修改 `.hermes.md` 的注入行为（保持全量）
- 修改 SOUL.md 的加载逻辑
- 引入新的配置项（用代码参数控制，后续可加 config.yaml 开关）

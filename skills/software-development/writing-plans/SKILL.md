---
name: writing-plans
description: >
  Creates comprehensive implementation plans with bite-sized tasks, exact file paths,
  and complete code examples. Use when you have a spec or requirements for a multi-step task.
trigger:
  - "write a plan"
  - "create a plan"
  - "implementation plan"
  - "how do I implement"
  - "做计划"
  - "实施计划"
  - "implementation"
  - "开发计划"
  - "task breakdown"
anti_trigger:
  - "single step"  # 一步就完成不需要做计划
  - "already have a plan"  # 已有计划不需要再写
  - "我知道怎么做"  # 用户已知道怎么做
source: hermes-agent (adapted from obra/superpowers)
version: 2.0.0
metadata:
  hermes:
    quality_redlines:
      - MUST have E (Execution) section
      - MUST have B (Boundary) section
      - MUST have A2 (Trigger) section
    tags: [planning, design, implementation, workflow, documentation]
    related_skills: [subagent-driven-development, test-driven-development, requesting-code-review]
---

## A2 — 触发场景 (Trigger) ★

**激活条件：** 有 spec 或需求，涉及多步骤任务，需要创建实施计划。

**触发信号语言：**
- "write a plan"、"create a plan"、"implementation plan"
- "how do I implement"、"做计划"、"实施计划"、"implementation"、"开发计划"
- "task breakdown"
- 任何多步骤功能实现需求

**区分相邻 skill：**
- `spec-driven-development`：产出规格文档，本 skill 基于规格产出实施计划
- `subagent-driven-development`：执行本 skill 创建的计划
- `idea-refine`：把想法精炼为可执行方案，本 skill 基于已有方案做实施计划

**Skip 场景：** 一步就完成、已有计划、用户已知道怎么做。

---

## R — 知识溯源 (Reading)

**核心原则（来源：obra/superpowers）：** A good plan makes implementation obvious. 如果有人需要猜，计划就不完整。

**核心假设：** 假设实施者是个有技能的开发者，但对工具集或问题域几乎一无所知。假设他们不太懂好的测试设计。

**Plan 必须包含的内容：** 哪些文件要改、完整代码、测试命令、要检查的文档、如何验证。给他们小而清晰的任务。

---

## I — 方法论骨架 (Interpretation)

**本 skill 的本质：** 把规格变成可执行的行动计划。每个任务 2-5 分钟专注工作，包含完整代码示例、精确文件路径和可执行的验证命令。

**为什么需要 bite-sized tasks？**
- 2-5 分钟任务容易 review
- 失败容易定位（如果 task 太粗，失败不知道在哪）
- 每次小成功积累 momentum

**Plan vs Spec：**
- Spec = 我们要构建什么、为什么
- Plan = 我们如何一步步构建、每个步骤验证什么

---

## A1 — 实践案例 (Past Application)

**反面教训：**
- **反面1：task 太粗** → "实现认证系统"（50 行代码跨 5 个文件），reviewer 不知道从哪审起，失败也不知道在哪。改成精确的小任务
- **反面2：代码示例不完整** → "添加验证函数"（没有代码），implementer 随便写了个错的。计划必须包含完整可 copy-paste 的代码
- **反面3：没有验证步骤** → "测试一下是否工作"，implementer 没跑测试就 commit 了。计划必须包含具体命令和期望输出

---

## E — 可执行步骤 (Execution) ★

### Step 1 — Understand Requirements

读取并理解：
- 功能需求
- 设计文档或用户描述
- 验收标准
- 约束条件

### Step 2 — Explore the Codebase

使用 Hermes tools 理解项目：

```python
# 理解项目结构
search_files("*.py", target="files", path="src/")

# 找类似功能
search_files("similar_pattern", path="src/", file_glob="*.py")

# 检查现有测试
search_files("*.py", target="files", path="tests/")

# 读关键文件
read_file("src/app.py")
```

### Step 3 — Design Approach

决定：
- 架构模式
- 文件组织
- 依赖
- 测试策略

### Step 4 — Write Tasks

按顺序创建任务：
1. Setup/infrastructure
2. Core functionality（TDD 每个）
3. Edge cases
4. Integration
5. Cleanup/documentation

### Plan Document Structure

**Header（必须）：**

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

**Task Structure：**

```markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
```

### Step 5 — Add Complete Details

每个任务包含：
- **精确文件路径**（不是"配置文件"而是 `src/config/settings.py`）
- **完整代码示例**（不是"添加验证"而是具体代码）
- **精确命令**含期望输出
- **验证步骤**证明任务工作

### Step 6 — Review the Plan

检查：
- [ ] 任务顺序合理
- [ ] 每个任务小而清晰（2-5 min）
- [ ] 文件路径精确
- [ ] 代码示例完整（可 copy-paste）
- [ ] 命令精确含期望输出
- [ ] 无缺失上下文
- [ ] DRY, YAGNI, TDD 原则应用

### Step 7 — Save the Plan

```bash
mkdir -p docs/plans
# Save plan to docs/plans/YYYY-MM-DD-feature-name.md
git add docs/plans/
git commit -m "docs: add implementation plan for [feature]"
```

---

## B — 边界 (Boundary) ★

**反场景（NOT this skill）：**
- 一步就完成 → 不需要做计划
- 已有计划 → 不重复写
- 用户已知道怎么做 → 不要过度计划

**邻近方法论区分：**
- **本 skill vs spec-driven-development**：spec 产出规格，plan 基于规格产出实施计划
- **本 skill vs subagent-driven-development**：本 skill 创建计划，subagent-driven-development 执行计划
- **本 skill vs idea-refine**：idea-refine 精炼想法，plan 基于想法做实施规划

**常见错误：**
| 错误 | 正确 |
|------|------|
| "Add authentication" | "Create User model with email and password_hash fields" |
| "Add validation function" | 完整 function 代码 |
| "Test it works" | `pytest tests/test_auth.py -v`，期望：3 passed |
| "Create the model file" | Create: `src/models/user.py` |

---

## Principles

### DRY (Don't Repeat Yourself)
**Bad:** Copy-paste validation in 3 places
**Good:** Extract validation function, use everywhere

### YAGNI (You Aren't Gonna Need It)
**Bad:** Add "flexibility" for future requirements
**Good:** Implement only what's needed now

### TDD (Test-Driven Development)
每个产生代码的任务都包含完整 TDD cycle：
1. 写失败测试
2. 跑测试验证失败
3. 写最小实现
4. 跑测试验证通过

### Frequent Commits
每个任务后 commit：
```bash
git add [files]
git commit -m "type: description"
```

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**

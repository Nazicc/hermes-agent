---
name: subagent-driven-development
description: >
  Executes implementation plans via fresh delegate_task per task with two-stage review:
  spec compliance first, then code quality.
  Use when executing multi-task plans from writing-plans skill.
trigger:
  - "run the plan"
  - "execute the plan"
  - "implement the plan"
  - "start implementing"
  - "开始执行"
  - "开始实现"
  - "run subagent"
  - "dispatch subagent"
anti_trigger:
  - "single file"  # 单文件改动不需要subagent编排
  - "one task only"  # 只有一个任务不需要subagent驱动
  - "不需要并行"
source: hermes-agent (adapted from obra/superpowers)
version: 2.0.0
metadata:
  hermes:
    quality_redlines:
      - MUST have E (Execution) section
      - MUST have B (Boundary) section
      - MUST have A2 (Trigger) section
    tags: [delegation, subagent, implementation, workflow, parallel]
    related_skills: [writing-plans, requesting-code-review, test-driven-development]
---

## A2 — 触发场景 (Trigger) ★

**激活条件：** 用户有一个实现计划（来自 `writing-plans` skill 或需求），要开始执行。

**触发信号语言：**
- "run the plan"、"execute the plan"、"implement the plan"、"start implementing"
- "开始执行"、"开始实现"、"run subagent"、"dispatch subagent"
- 任何来自 `writing-plans` skill 的计划，要求按任务执行

**区分相邻 skill：**
- `writing-plans`：制定计划，本 skill 执行计划
- `requesting-code-review`：本 skill 的 two-stage review（spec compliance + code quality）即是 code review 的质量门控
- `test-driven-development`：TDD 嵌入在本 skill 的 implementer subagent 上下文中

**Skip 场景：** 单文件改动、只有一个任务、不需要并行执行。

---

## R — 知识溯源 (Reading)

**核心原则（来源：obra/superpowers）：** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

**设计来源：**
1. **Fresh context per task**：防止上下文污染（context pollution），每个 subagent 获得干净、聚焦的上下文
2. **Two-stage review**：Spec review 先于 code quality review，避免在不符合 spec 的代码上做质量优化
3. **Never skip reviews**：reviewer 发现问题 → implementer 修复 → reviewer 再次审查，不跳过 re-review

**效率权衡：** subagent 调用次数多（每个任务 1 implementer + 2 reviewers），但问题在早期捕获，总成本更低。

---

## I — 方法论骨架 (Interpretation)

**本 skill 的本质：** 把大型实现计划分解为独立任务，每个任务由 fresh subagent 执行，执行后经过 spec compliance + code quality 双重审查，再进入下一个任务。

**为什么需要 two-stage review？**
- Spec review 先于 quality review：防止在错误的实现上做优化
- Spec review 捕获 under-building（没做完）和 over-building（做多了）
- Quality review 确保实现是 well-built 的
- 两者缺一不可

**为什么需要 fresh subagent per task？**
- 防止 context pollution：之前任务的代码或推理不会污染新任务
- 每个 subagent 获得干净、聚焦的上下文
- 不可能让 implementer 自己 review 自己（confirmation bias）

---

## A1 — 实践案例 (Past Application)

**反面教训（来源：obra/superpowers feedback）：**
- **反面1：review 顺序颠倒** → code quality review 先于 spec compliance，结果代码很漂亮但不符合 spec，整个重写。先 spec 再 quality
- **反面2：skip re-review** → reviewer 发现问题，implementer 修复后直接继续，没有再次 review，同样的问题又出现。加了"不要 skip re-review"规则
- **反面3：让 implementer 自己 review** → confirmation bias 导致 implementer 看不到自己的问题。引入独立 reviewer subagent
- **反面4：subagent 不读 plan 文件** → subagent 读 plan 时丢失上下文，实现跑偏。要求在 context 里直接提供完整 task 文本

---

## E — 可执行步骤 (Execution) ★

### The Process

```
Read Plan → Create todo list → Per-task: Implement → Spec Review → Quality Review → Mark Complete
```

### Step 1 — Read and Parse Plan

读取计划文件，一次性提取所有任务和上下文：

```python
read_file("docs/plans/feature-plan.md")

todo([
    {"id": "task-1", "content": "Create User model with email field", "status": "pending"},
    {"id": "task-2", "content": "Add password hashing utility", "status": "pending"},
    {"id": "task-3", "content": "Create login endpoint", "status": "pending"},
])
```

**关键：读 plan 一次，读完。不让 subagent 自己读 plan 文件——把完整 task 文本直接放在 context 里。**

### Step 2 — Per-Task Workflow

对计划中的每个任务，顺序执行：

#### 2a. Dispatch Implementer Subagent

```python
delegate_task(
    goal="Implement Task 1: Create User model with email and password_hash fields",
    context="""
    TASK FROM PLAN:
    - Create: src/models/user.py
    - Add User class with email (str) and password_hash (str) fields
    - Use bcrypt for password hashing
    - Include __repr__ for debugging

    FOLLOW TDD:
    1. Write failing test in tests/models/test_user.py
    2. Run: pytest tests/models/test_user.py -v (verify FAIL)
    3. Write minimal implementation
    4. Run: pytest tests/models/test_user.py -v (verify PASS)
    5. Run: pytest tests/ -q (verify no regressions)
    6. Commit: git add -A && git commit -m "feat: add User model with password hashing"

    PROJECT CONTEXT:
    - Python 3.11, Flask app in src/app.py
    - Existing models in src/models/
    - Tests use pytest, run from project root
    - bcrypt already in requirements.txt
    """,
    toolsets=['terminal', 'file']
)
```

**如果 subagent 问问题：** 清晰完整回答，提供额外上下文，不要 rush。

#### 2b. Dispatch Spec Compliance Reviewer（spec review 先于 quality review）

```python
delegate_task(
    goal="Review if implementation matches the spec from the plan",
    context="""
    ORIGINAL TASK SPEC:
    - Create src/models/user.py with User class
    - Fields: email (str), password_hash (str)
    - Use bcrypt for password hashing
    - Include __repr__

    CHECK:
    - [ ] All requirements from spec implemented?
    - [ ] File paths match spec?
    - [ ] Function signatures match spec?
    - [ ] Behavior matches expected?
    - [ ] Nothing extra added (no scope creep)?

    OUTPUT: PASS or list of specific spec gaps to fix.
    """,
    toolsets=['file']
)
```

**如果 spec 不合规：** 修复 gaps，然后 re-run spec review。只有 spec 通过后才能进入 quality review。

#### 2c. Dispatch Code Quality Reviewer

```python
delegate_task(
    goal="Review code quality for Task 1 implementation",
    context="""
    FILES TO REVIEW:
    - src/models/user.py
    - tests/models/test_user.py

    CHECK:
    - [ ] Follows project conventions and style?
    - [ ] Proper error handling?
    - [ ] Clear variable/function names?
    - [ ] Adequate test coverage?
    - [ ] No obvious bugs or missed edge cases?
    - [ ] No security issues?

    OUTPUT FORMAT:
    - Critical Issues: [must fix before proceeding]
    - Important Issues: [should fix]
    - Minor Issues: [optional]
    - Verdict: APPROVED or REQUEST_CHANGES
    """,
    toolsets=['file']
)
```

**如果 quality 问题：** 修复，re-review。只有 approved 后才能进入下一个任务。

#### 2d. Mark Task Complete

```python
todo([{"id": "task-1", "status": "completed"}], merge=True)
```

### Step 3 — Final Integration Review

所有任务完成后，dispatch 最终集成审查：

```python
delegate_task(
    goal="Review the entire implementation for consistency and integration issues",
    context="""
    All tasks from the plan are complete. Review the full implementation:
    - Do all components work together?
    - Any inconsistencies between tasks?
    - All tests passing?
    - Ready for merge?
    """,
    toolsets=['terminal', 'file']
)
```

### Step 4 — Verify and Commit

```bash
pytest tests/ -q
git diff --stat
git add -A && git commit -m "feat: complete [feature name] implementation"
```

---

## Task Granularity

**每个任务 = 2-5 分钟专注工作。**

| 太粗 | 正确 |
|------|------|
| "Implement user authentication system" | "Create User model with email and password fields" |
| | "Add password hashing function" |
| | "Create login endpoint" |
| | "Add JWT token generation" |
| | "Create registration endpoint" |

---

## B — 边界 (Boundary) ★

**反场景（NOT this skill）：**
- 单文件改动 → 不需要 subagent 编排，直接实现
- 只有一个任务 → 不需要 subagent 驱动
- 不需要并行 → 直接顺序执行

**邻近方法论区分：**
- **本 skill vs writing-plans**：writing-plans = 制定计划，本 skill = 执行计划
- **本 skill vs requesting-code-review**：本 skill 的 two-stage review 本身就是 code review；requesting-code-review 是提交前自查
- **本 skill vs test-driven-development**：TDD 作为嵌入了 implementer subagent 的上下文

**已知失败模式：**
- **code quality review 先于 spec compliance** → 代码漂亮但不对，重写。顺序必须是 spec first
- **skip re-review** → 同样的问题重复出现。reviewer 发现问题 → implementer 修复 → 必须 re-review
- **implementer self-review** → confirmation bias，引入独立 reviewer
- **subagent 自己读 plan 文件** → 上下文丢失，在 context 里直接提供完整 task 文本
- **review 有 open issues 仍继续下一个任务** → 问题会 compound，必须修复后才能继续
- **scope creep** → implementer 添加了 spec 里没有的东西，spec review 捕获

## Remember

```
Fresh subagent per task
Two-stage review every time
Spec compliance FIRST
Code quality SECOND
Never skip reviews
Catch issues early
```

**Quality is not an accident. It's the result of systematic process.**

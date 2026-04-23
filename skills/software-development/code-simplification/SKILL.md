---
name: code-simplification
description: >
  Simplifies code for clarity without changing behavior.
  Use when code works but is harder to read, maintain, or extend than it should be.
  Use when refactoring code for clarity.
  Use when encountering deeply nested logic, long functions, or unclear names.
trigger:
  - "simplify"
  - "simplify this code"
  - "重构"
  - "clean up"
  - "代码太复杂"
  - "代码简化"
  - " readability"
  - "可读性"
  - "太乱了"
anti_trigger:
  - "it works fine, leave it alone"  # 代码本来就清晰，不需要简化
  - "performance critical"  # 性能关键路径，不是简化场景
  - "I don't understand what this code does yet"  # 不理解代码时不要简化
  - "rewrite from scratch"  # 全新重写不是简化
  - "我不懂这段代码"
source: hermes-agent (inspired by anthropics/claude-code plugins/code-simplifier)
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

**激活条件：** 代码功能正常但过于复杂、难以理解或维护。

**触发信号语言：**
- "simplify"、"simplify this code"、"重构"、"clean up"
- "代码太复杂"、"代码简化"、"readability"、"可读性"、"太乱了"
- 代码 review 中标记的可读性/复杂度问题
- 功能 working 后感觉实现比需要的重

**区分相邻 skill：**
- `incremental-implementation`：增量是交付方法，本 skill 是代码质量方法
- `requesting-code-review`：审核是改前验证，本 skill 是改后美化
- 本 skill 不改变行为，只是让代码更易理解

**Skip 场景：**
- 代码本来就清晰 — 不要为了简化而简化
- 你还不理解代码在做什么 — 先理解再简化（Chesterton's Fence）
- 性能关键路径 — 简化可能引入性能问题
- 准备全新重写 — 简化废弃代码是浪费精力

---

## R — 知识溯源 (Reading)

**来源：** Anthropics Claude Code code-simplifier plugin (model-agnostic adaptation)

**核心原则：** 简化不是减少行数，而是让代码更易理解。目标不是"I could read this in 30 seconds"，而是"A new team member would understand this faster than the original."

**五条原则（来源）：**
1. **Preserve Behavior Exactly** — 只改变表达方式，不改变行为
2. **Follow Project Conventions** — 简化要符合 codebase 风格，不是外来偏好
3. **Prefer Clarity Over Cleverness** — 显式代码优于紧凑代码
4. **Maintain Balance** — 过度简化是另一种复杂度
5. **Scope to What Changed** — 默认只简化最近改动的代码

**Chesterton's Fence（本 skill 的元原则）：** 如果你看到代码里有一道 fence，但不理解为什么它在那里，不要把它拆掉。先理解原因，再决定是否移除。

---

## I — 方法论骨架 (Interpretation)

**本 skill 的本质：** 在行为严格不变的前提下，通过减少表达复杂度让代码更易理解。不是重构功能，是重构可读性。

**简化 vs 重构：**
- 重构（refactor）：改变代码结构，可能改变行为
- 简化（simplify）：改变表达方式，行为严格不变
- 两者通常一起发生，但本 skill 专注于后者

**简化有失败模式：**
- **过度简化**：删除有用的 helper function（它给概念命名了），反而让 call site 难读
- **合并无关逻辑**：两个简单函数合并成一个复杂函数，不是简化
- **移除"不必要"的抽象**：有些抽象是为了可扩展性或可测试性，不是过度设计
- **优化行数**：行数少不是目标，理解速度快才是目标

**信号系统（不是模糊的"code smell"）：**

| 类型 | 信号 | 简化方式 |
|------|------|---------|
| 结构复杂度 | 3+ 层嵌套 | guard clause / helper function |
| 结构复杂度 | 50+ 行函数 | 拆分为单一职责函数 |
| 结构复杂度 | 嵌套 ternary | if/else 链或 lookup object |
| 结构复杂度 | 布尔参数 flags | options object 或分函数 |
| 命名 | 通用名 data/result/temp/val/item | 改为描述内容 |
| 命名 | 缩写 usr/cfg/btn/evt | 用完整词（除非 universal 如 id/url/api）|
| 命名 | 误导性名称 | 改为反映实际行为 |
| 冗余 | 重复逻辑（5+ 行相同）| 提取到共享函数 |
| 冗余 | 死代码 unreachable/unused | 确认后删除 |
| 冗余 | 无价值 wrapper | inline wrapper |

---

## A1 — 实践案例 (Past Application)

**反面教训：**
- **反面1：删了 helper 反而难读** → 原来 `formatUserName(name)` 是个 helper，简化时 inline 了，但 call site 有三处，每处都要读一遍格式化逻辑。Helper 给了概念名字，是有价值的
- **反面2：合并了两个无关函数** → `process()` 原来调用 `validate()` 和 `transform()`，分别因为两个不同原因调用。合并后函数职责不清。保持分离
- **反面3：删了 error handling** → 觉得 try/catch "让代码不干净"，删了。结果线上 NPE。简化不能削弱错误处理
- **反面4：改了不理解的代码** → git blame 显示这段代码是为了处理一个历史 bug 加的，简化时没注意，后来 bug 重现。先理解再简化

---

## E — 可执行步骤 (Execution) ★

### Step 1 — Understand Before Touching（Chesterton's Fence）

先灵魂拷问：

```
BEFORE SIMPLIFYING, ANSWER:
- What is this code's responsibility?
- What calls it? What does it call?
- What are the edge cases and error paths?
- Are there tests that define the expected behavior?
- Why might it have been written this way?
  (Performance? Platform constraint? Historical reason?)
- Check git blame: what was the original context?
```

**如果回答不了这些问题，先去读更多上下文。**

### Step 2 — Identify Simplification Opportunities

扫描以下具体信号：

**Structural complexity：**
- Deep nesting（3+ levels）→ Extract conditions into guard clauses or helper functions
- Long functions（50+ lines）→ Split into focused functions with descriptive names
- Nested ternaries → Replace with if/else chains, switch, or lookup objects
- Boolean parameter flags → `doThing(true, false, true)` → Replace with options objects
- Repeated conditionals → Extract to a well-named predicate function

**Naming：**
- Generic names → Rename: `data` → `userProfile`, `result` → `validationErrors`
- Abbreviated names → Full words: `usr` → `user`, `cfg` → `config`
- Misleading names → Rename to reflect actual behavior
- Comments explaining "what" → Delete（code is self-explanatory）
- Comments explaining "why" → Keep（intent cannot be expressed in code）

**Redundancy：**
- Duplicated logic → Extract to shared function
- Dead code → Remove after confirming truly dead
- Unnecessary abstraction → Inline, call underlying function directly
- Over-engineered patterns → Replace with simple direct approach
- Redundant type assertions → Remove

### Step 3 — Apply Changes Incrementally

一次只做一个简化，测试后提交：

```
FOR EACH SIMPLIFICATION:
1. Make the change
2. Run the test suite
3. If tests pass → commit (or continue to next simplification)
4. If tests fail → revert and reconsider
```

**The Rule of 500：** 如果一个 refactoring 要改动超过 500 行，用自动化工具（codemods、AST transforms），不要手工改。

**不要混合改动：** Refactoring PR 和 feature/bug-fix PR 分开。一个 PR 做了简化又加了功能，reviewer 会头疼。

### Step 4 — Verify the Result

回头评估：

```
COMPARE BEFORE AND AFTER:
- Is the simplified version genuinely easier to understand?
- Did I introduce any new patterns inconsistent with the codebase?
- Is the diff clean and reviewable?
- Would a teammate approve this change?
```

如果"简化版"反而更难理解或 review，回滚。不是每次简化都成功。

---

## B — 边界 (Boundary) ★

**反场景（NOT this skill）：**
- 代码本来就清晰可读 — 不要简化
- 不理解代码在做什么 — 先理解，不要简化
- 性能关键路径 — 简化可能引入性能问题，需要 benchmark
- 准备全新重写 — 简化 throwaway code 浪费精力

**邻近方法论区分：**
- **本 skill vs incremental-implementation**：增量是交付方法，简化是代码质量方法；增量在实现过程中，简化在实现完成后
- **本 skill vs requesting-code-review**：审核是改前验证，简化是改后美化；两者经常配合使用
- **本 skill vs refactoring（一般意义的）**：简化严格不改变行为，重构可能改变行为

**简化失败模式：**
- 简化后测试需要修改 → 你可能改变了行为
- "简化版"比原版更长更难理解 → 回滚
- 用个人偏好重命名而非项目惯例 → 不要简化
- 删除了错误处理让代码"更干净" → 错误处理不能删
- 简化不懂的代码 → Chesterton's Fence

**常见合理化（及其真相）：**

| Rationalization | Reality |
|---|---|
| "能用就行，不用动它" | 工作但难读的代码，未来每次修改都要额外时间 |
| "行数少就是简单" | 1 行嵌套 ternary 不比 5 行 if/else 简单 |
| "顺手把无关代码也简化了" | 无关改动制造噪音 diff，引入回归风险 |
| "类型让代码自文档化" | 类型记录结构，不记录意图。好名字比类型更能解释为什么 |
| "这个抽象以后可能有用" |  speculative abstraction 没有价值。等第三个 use case 出现再加 |
| "原作者肯定有原因" | 查 git blame — 应用 Chesterton's Fence。但积累的复杂度通常没有原因，只是压力下的残留 |

---

## Language-Specific Guidance

### TypeScript / JavaScript

```typescript
// SIMPLIFY: Unnecessary async wrapper
// Before
async function getUser(id: string): Promise<User> {
  return await userService.findById(id);
}
// After
function getUser(id: string): Promise<User> {
  return userService.findById(id);
}

// SIMPLIFY: Verbose conditional assignment
// Before
let displayName: string;
if (user.nickname) {
  displayName = user.nickname;
} else {
  displayName = user.fullName;
}
// After
const displayName = user.nickname || user.fullName;

// SIMPLIFY: Manual array building
// Before
const activeUsers: User[] = [];
for (const user of users) {
  if (user.isActive) {
    activeUsers.push(user);
  }
}
// After
const activeUsers = users.filter((user) => user.isActive);
```

### Python

```python
# SIMPLIFY: Verbose dictionary building
# Before
result = {}
for item in items:
    result[item.id] = item.name
# After
result = {item.id: item.name for item in items}

# SIMPLIFY: Nested conditionals with early return
# Before
def process(data):
    if data is not None:
        if data.is_valid():
            if data.has_permission():
                return do_work(data)
            else:
                raise PermissionError("No permission")
        else:
            raise ValueError("Invalid data")
    else:
        raise TypeError("Data is None")
# After
def process(data):
    if data is None:
        raise TypeError("Data is None")
    if not data.is_valid():
        raise ValueError("Invalid data")
    if not data.has_permission():
        raise PermissionError("No permission")
    return do_work(data)
```

### React / JSX

```tsx
// SIMPLIFY: Verbose conditional rendering
// Before
function UserBadge({ user }: Props) {
  if (user.isAdmin) {
    return <Badge variant="admin">Admin</Badge>;
  } else {
    return <Badge variant="default">User</Badge>;
  }
}
// After
function UserBadge({ user }: Props) {
  const variant = user.isAdmin ? 'admin' : 'default';
  const label = user.isAdmin ? 'Admin' : 'User';
  return <Badge variant={variant}>{label}</Badge>;
}
```

## Red Flags

- Simplification that requires modifying tests to pass（你可能改变了行为）
- "简化版"比原版更长更难 follow
- 用个人偏好重命名而非项目惯例
- 删除了错误处理让代码"更干净"
- 简化不懂的代码
- 批量多个简化到一个难以 review 的大 PR
- 改动 scope 外的代码（未经用户明确要求）

## Verification

简化完成后验证：
- [ ] 所有现有测试通过，不需要修改
- [ ] 构建成功，无新警告
- [ ] Linter/formatter 通过（无风格回归）
- [ ] 每个简化都是 incremental、reviewable 的
- [ ] Diff 干净 — 无无关改动混入
- [ ] 简化后的代码符合项目惯例
- [ ] 没有删除或削弱错误处理
- [ ] 没有死代码残留（未使用的 imports、无可达分支）
- [ ] 队友或 review agent 会 approve 这个改动

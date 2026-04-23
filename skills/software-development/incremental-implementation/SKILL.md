---
name: incremental-implementation
description: >
  Delivers changes incrementally — thin vertical slices, test each, verify each, commit each.
  Use when implementing any feature or change that touches more than one file.
  Use when you're about to write a large amount of code at once, or when a task feels too big to land in one step.
trigger:
  - "implement"
  - "开始实现"
  - "开始写代码"
  - "写代码"
  - "implement feature"
  - "实现功能"
  - "how do I build"
  - "怎么实现"
  - "refactor"
  - "重构"
anti_trigger:
  - "single line"  # 单行改动不需要增量
  - "one function"  # 单函数改动不需要增量
  - "trivial"  # trivial 改动不需要增量
  - "只改一行"
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

**激活条件：** 用户要求实现任何功能、重构代码，或任何涉及多个文件的改动。

**触发信号语言：**
- "implement"、"开始实现"、"开始写代码"、"写代码"、"实现功能"
- "how do I build"、"怎么实现"、"refactor"、"重构"
- 任何涉及 2+ 文件改动的任务
- 任何感觉"太大无法一次搞定"的任务

**区分相邻 skill：**
- `test-driven-development`：TDD 是先写测试再实现，本 skill 是实现过程中的切片方法论
- `code-simplification`：简化是在行为不变的前提下减少复杂度，本 skill 是交付行为的增量方式
- `requesting-code-review`：提交审核，本 skill 是如何切分实现

**Skip 场景：** 单行改动、单函数改动、trivial 改动。

---

## R — 知识溯源 (Reading)

**Vertical Slice（垂直切片）原则：** 不要横向铺开所有层（DB → API → UI 全部写完再测试），而是纵向切穿每一层（DB + API → 测试 → UI → 测试）。

**核心思想来源：** Software engineering tradition — iterate in thin, verifiable increments. 每个 increment 结束时应处于可测试、可回滚的状态。

**Rule 0（最重要）：Simplicity First** — 每次问自己"最简单的能工作的版本是什么？"实现明显正确的版本在优化之前。

**Rule 0.5：Scope Discipline** — 只改任务需要的，不碰相邻代码。"顺手优化"是最大的增量交付敌人。

---

## I — 方法论骨架 (Interpretation)

**本 skill 的本质：** 把大型实现任务分解为最小可交付单元的方法论。每个单元独立测试、独立提交，形成可回滚、可审查的交付链。

**为什么需要增量而不是一次实现全部？**
1. **Bug 定位**：一次改 500 行，出 bug 不知道哪行导致；一次改 30 行，出问题立即知道
2. **Code review 友好**：小 diff 容易审查，大 diff 审查者容易遗漏问题
3. **回滚成本低**：每个 increment 可独立回滚；一次写完再回滚代价大
4. **验证节奏感**：每步都有完成感，防止"写了一大堆不知道对不对"的焦虑

**三种切片策略：**
- **Vertical Slice（最优）**：切穿全栈，每个 slice 都能端到端运行
- **Contract-First**：先定义接口，再前后端分别实现（适合前后端分离）
- **Risk-First**：先做风险最高的（通常是网络/IO/并发相关）

---

## A1 — 实践案例 (Past Application)

**反面教训：**
- **反面1：不做增量，最后一起测** → 500 行改完，测试失败，不知道哪行问题，花 3 小时 bisect。如果拆成 10 个 slice，每个 50 行，出问题立即知道在哪个 slice
- **反面2：scope creep** → "我顺手把隔壁模块也重构了"，结果 review 时审查者发现改动范围太大，拒绝整个 PR。Rule 0.5 的核心教训
- **反面3：过早抽象** → 写了一个 EventBus 通用中间件，实际上只用于一个通知系统。后来 EventBus 有 bug，因为只有一个人懂。垂直切片避免过早抽象
- **反面4：增量改完不 commit** → 积累了大量 uncommitted changes，突然需要回滚发现无法精确回滚。每个 slice 完成后立即 commit

---

## E — 可执行步骤 (Execution) ★

### The Increment Cycle

```
Implement ──→ Test ──→ Verify ──→ Commit ──→ Next slice
     ▲                                        │
     └────────── Rollback if failed ◄──────────┘
```

### Step 1 — Define the first slice

确定第一个 slice 的范围：
- **最小可工作单元**：能运行、能测试、能验证
- **不求完美**：只实现明确需要的，不做扩展
- **穿全栈**：如果做 CRUD，第一个 slice 应该能 Create 并从 DB 读取，不只是写 DB 层

```bash
# 确认这是一个 git repo
git status || exit 0
```

### Step 2 — Implement the slice

根据任务类型选择切片策略：

**Vertical Slice（推荐）：**
```
Slice 1: DB schema + API endpoint + basic UI (可以运行)
Slice 2: List 功能
Slice 3: Update 功能
Slice 4: Delete 功能
```

**Contract-First Slice：**
```
Slice 0: 定义 API contract（类型、接口）
Slice 1a: 后端实现 contract + API tests
Slice 1b: 前端 mock 数据实现
Slice 2: 集成测试
```

**Risk-First Slice：**
```
Slice 1: 先做最高风险部分（WebSocket 连接、外部 API 调用）
Slice 2: 在已验证的连接上构建业务逻辑
Slice 3: 添加离线支持
```

### Step 3 — Simplicity Check（每次实现前必问）

```
ASK BEFORE WRITING CODE:
→ What is the simplest thing that could work?
→ Can this be done in fewer lines?
→ Are these abstractions earning their complexity?
→ Would a staff engineer say "why didn't you just..."?
→ Am I building for hypothetical future requirements?
```

**典型错误 vs 正确：**
```
✗ Generic EventBus with middleware pipeline for one notification
✓ Simple function call

✗ Abstract factory pattern for two similar components
✓ Two straightforward components with shared utilities

✗ Config-driven form builder for three forms
✓ Three form components
```

### Step 4 — Test and verify

每个 slice 后必须验证：

```bash
# 测试（根据项目语言）
python -m pytest --tb=short 2>&1 | tail -10
npm test 2>&1 | tail -10
cargo test 2>&1 | tail -10

# 构建
npm run build 2>&1 | tail -5
cargo build 2>&1 | tail -5

# 类型检查
npx tsc --noEmit 2>&1 | tail -5
```

### Step 5 — Scope Discipline（Scope Creep Prevention）

**Do NOT：**
- "顺手" clean up 相邻改动
- 重构你只读的文件的 imports
- 删除你不完全理解的注释
- 添加 spec 里没有的功能（"感觉有用"不是理由）
- 在你只读的文件里 modernizing syntax

**如果你注意到 scope 外的东西：**
```
NOTICED BUT NOT TOUCHING:
- src/utils/format.ts has an unused import (unrelated to this task)
- The auth middleware could use better error messages (separate task)
→ Want me to create tasks for these?
```

### Step 6 — Commit

```bash
git add -A && git commit -m "[increment] <description of what this slice does>"
```

每个 slice 独立 commit，描述这个 slice 做了什么，不是整个任务。

### Step 7 — Repeat for next slice

带着已 commit 的改动继续下一个 slice，不 restart。

---

## B — 边界 (Boundary) ★

**反场景（NOT this skill）：**
- 单行、单函数、trivial 改动 → 不需要走完整增量流程
- 纯文档修改 → 不需要增量
- 纯配置调整 → 不需要增量

**邻近方法论区分：**
- **本 skill vs test-driven-development**：TDD = 先写测试再写实现（心态），增量 = 如何切分实现（执行方法）
- **本 skill vs code-simplification**：简化是改完后的重构，本 skill 是交付过程中的切片方法
- **本 skill vs requesting-code-review**：审核在增量之后，本 skill 是如何切分实现

**已知失败模式：**
- "一次写完再测" → Bug 定位成本指数增长
- "顺手优化 scope 外的东西" → PR 范围爆炸，reviewer 拒绝
- "先过度抽象再简化" → EventBus 陷阱；等到第 3 个 use case 出现再考虑抽象
- "增量改完不 commit" → 大量 uncommitted 堆积，回滚困难
- "跳过测试/验证步骤" → Bug 快速积累，最终难以收拾

**Feature Flag（当增量无法完全交付时）：**

```typescript
const ENABLE_FEATURE_X = process.env.FEATURE_X === 'true';

if (ENABLE_FEATURE_X) {
  // New sharing UI
}
```

合并到 main 分支但不需要用户可见的功能用 feature flag 保护。

## Increment Checklist

每个 slice 后验证：
- [ ] 改动做了一件事，完整地做了
- [ ] 现有测试仍然通过（`npm test` / `pytest`）
- [ ] 构建成功（`npm run build` / `cargo build`）
- [ ] 类型检查通过（`tsc --noEmit`）
- [ ] Linting 通过（`npm run lint`）
- [ ] 新功能按预期工作
- [ ] 改动已 commit，描述清晰

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "最后一起测" | Bug 会在每个 slice 里积累，最后不知道哪行导致 |
| "一次搞定更快" | 感觉快，直到出问题。50 行的 bug 比 500 行好定位 10 倍 |
| "这些改动太小不值得单独 commit" | 小 commit 免费。大 commit 隐藏 bug，让回滚痛苦 |
| "feature flag 后面再加" | 如果功能没完成，就不应该让用户可见。现在加 flag |
| "重构很小可以混进来" | 重构和功能混合让两者都更难审查和调试 |

## Verification

任务全部完成后：
- [ ] 每个 increment 都单独测试和 commit
- [ ] 完整测试套件通过
- [ ] 构建干净
- [ ] 功能按 spec 端到端工作
- [ ] 没有 uncommitted changes

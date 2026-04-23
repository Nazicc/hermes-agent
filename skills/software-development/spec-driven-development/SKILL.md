---
name: spec-driven-development
description: >
  Creates specs before coding. Use when starting a new project, feature, or significant change
  and no specification exists yet. Use when requirements are unclear, ambiguous, or only exist as a vague idea.
trigger:
  - "spec"
  - "write a spec"
  - "create a spec"
  - "starting a new project"
  - "开始新项目"
  - "写规格"
  - "规格说明书"
  - "specification"
  - "PRD"
  - "需求文档"
anti_trigger:
  - "single line"  # 单行改动不需要spec
  - "typo"  # typo修正不需要spec
  - "trivial"  # trivial改动不需要spec
  - "already have a spec"  # 已有spec时不需要再写
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

**激活条件：** 开始新项目、功能或重大变更，且尚无规格说明；需求模糊、不完整或只是模糊想法。

**触发信号语言：**
- "spec"、"write a spec"、"create a spec"、"starting a new project"
- "开始新项目"、"写规格"、"规格说明书"、"specification"、"PRD"、"需求文档"
- 需求不明确、不完整或只有模糊想法

**区分相邻 skill：**
- `writing-plans`：在 spec 之后制定实施计划，本 skill 产出 spec
- `idea-refine`：精炼想法为可执行方案，本 skill 把需求写成规格文档
- `spec-driven-development` 专注于"写规格"，`writing-plans` 专注于"如何执行"

**Skip 场景：** 单行改动、typo 修正、trivial 改动、已有 spec。

---

## R — 知识溯源 (Reading)

**核心原则：** Code without a spec is guessing. 规格文档是与人类工程师之间的共享真理——定义我们在构建什么、为什么、以及如何知道完成了。

**四阶段门控流程（来源）：**

```
SPECIFY ──→ PLAN ──→ TASKS ──→ IMPLEMENT
   │          │        │          │
   ▼          ▼        ▼          ▼
 Human      Human    Human      Human
 reviews    reviews  reviews    reviews
```

在进入下一阶段之前，当前阶段必须被验证。规格文档是 living document，不是一次性产出。

---

## I — 方法论骨架 (Interpretation)

**本 skill 的本质：** 在写代码之前先把规格写清楚。把模糊需求翻译成具体可测试的条件。

**为什么需要 spec？**
- 表面假设：模糊需求最大的危险是隐含假设，在代码写完后才发现代价极高
- Shared truth：spec 是你和用户之间的共享真理，避免"我以为你说的是..."
- 15 分钟 spec 防止 15 小时返工

**六个核心领域（规格必须覆盖）：**
1. **Objective** — 目标、用户、成功标准
2. **Commands** — 完整可执行命令（含 flags）
3. **Project Structure** — 源码、测试、文档目录
4. **Code Style** — 一段真实代码示例 > 三段描述
5. **Testing Strategy** — 测试框架、覆盖率期望
6. **Boundaries** — Always / Ask First / Never

---

## A1 — 实践案例 (Past Application)

**反面教训：**
- **反面1：没表面假设** → 实现了 session-based auth，结果用户要的是 JWT。15 分钟 spec vs 3 小时重写。假设必须明面列出
- **反面2：跳过 spec 直接实现** → 写了 500 行后发现 DB schema 不对，API 设计也有问题。Spec 的价值在于强制在写代码之前理清思路
- **反面3：spec 写了不 review** → spec 有漏洞但没让用户确认，实现完了才发现理解不一致。每次 spec 完成后必须让人类 review

---

## E — 可执行步骤 (Execution) ★

### Phase 1: Specify

从高层次愿景开始，问澄清问题直到需求具体。

**首先列出假设：**

```
ASSUMPTIONS I'M MAKING:
1. This is a web application (not native mobile)
2. Authentication uses session-based cookies (not JWT)
3. The database is PostgreSQL (based on existing Prisma schema)
4. We're targeting modern browsers only (no IE11)
→ Correct me now or I'll proceed with these.
```

**规格文档覆盖六个核心领域：**

1. **Objective** — 我们在构建什么、为什么、用户是谁、成功什么样

2. **Commands** — 完整可执行命令，不只是工具名
   ```
   Build: npm run build
   Test: npm test -- --coverage
   Lint: npm run lint --fix
   Dev: npm run dev
   ```

3. **Project Structure** — 源码在哪、测试在哪、文档在哪
   ```
   src/           → Application source code
   src/components → React components
   src/lib        → Shared utilities
   tests/         → Unit and integration tests
   e2e/           → End-to-end tests
   docs/          → Documentation
   ```

4. **Code Style** — 一个真实代码示例 > 三段描述。包括命名规范、格式规则、好输出示例。

5. **Testing Strategy** — 什么框架、测试在哪、覆盖率期望、哪些测试层级。

6. **Boundaries** — 三层系统：
   - **Always do：** 运行测试后再提交、遵循命名规范、校验输入
   - **Ask first：** 数据库 schema 变更、添加依赖、修改 CI 配置
   - **Never do：** 提交 secrets、编辑 vendor 目录、未经批准删除失败测试

**规格模板：**

```markdown
# Spec: [Project/Feature Name]

## Objective
[What we're building and why. User stories or acceptance criteria.]

## Tech Stack
[Framework, language, key dependencies with versions]

## Commands
[Build, test, lint, dev — full commands]

## Project Structure
[Directory layout with descriptions]

## Code Style
[Example snippet + key conventions]

## Testing Strategy
[Framework, test locations, coverage requirements, test levels]

## Boundaries
- Always: [...]
- Ask first: [...]
- Never: [...]

## Success Criteria
[How we'll know this is done — specific, testable conditions]

## Open Questions
[Anything unresolved that needs human input]
```

**把模糊需求重新定义为成功标准：**

```
REQUIREMENT: "Make the dashboard faster"

REFRAMED SUCCESS CRITERIA:
- Dashboard LCP < 2.5s on 4G connection
- Initial data load completes in < 500ms
- No layout shift during load (CLS < 0.1)
→ Are these the right targets?
```

### Phase 2: Plan

用已验证的 spec 生成技术实现计划：

1. 识别主要组件及依赖
2. 确定实现顺序（什么必须先构建）
3. 注意风险和缓解策略
4. 识别可并行 vs 必须顺序的部分
5. 定义阶段之间的验证 checkpoint

### Phase 3: Tasks

把计划分解为离散可执行任务：

- 每个任务可在单次聚焦会话中完成
- 每个任务有明确验收标准
- 每个任务包含验证步骤（测试、构建、手动检查）
- 任务按依赖排序，非按感知重要性
- 每个任务改动不超过约 5 个文件

**任务模板：**
```markdown
- [ ] Task: [Description]
  - Acceptance: [What must be true when done]
  - Verify: [How to confirm — test command, build, manual check]
  - Files: [Which files will be touched]
```

### Phase 4: Implement

使用 `incremental-implementation` 和 `test-driven-development` skills 按顺序执行任务。使用 `context-engineering` 在每个步骤加载正确的 spec 章节和源文件。

---

## B — 边界 (Boundary) ★

**反场景（NOT this skill）：**
- 单行修复、typo 修正 → 不需要 spec
- 需求已经明确且自包含 → 短 spec 即可，不需要 6 个领域全部覆盖
- 用户明确说不需要 spec → 尊重用户选择

**邻近方法论区分：**
- **本 skill vs writing-plans**：本 skill 产出规格文档，writing-plans 基于 spec 产出执行计划
- **本 skill vs idea-refine**：idea-refine 把想法精炼为方案，本 skill 把方案写成规格
- **本 skill vs spec-driven-development** vs **incremental-implementation**：spec → plan → implement 三层递进

**已知失败模式：**
- 没列出假设就开写 → 隐含假设导致后期大返工
- Spec 写了不让用户 review → 理解不一致，代码完成后才发现
- "简单任务不需要 spec" → 再简单的任务也需要验收标准
- "代码写完再补 spec" → 那是文档，不是规格；spec 的价值在于写代码之前强制澄清

---

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "这很简单，不需要 spec" | 简单任务不需要*长* spec，但仍需要验收标准 |
| "代码写完再补 spec" | 那是文档，不是规格。Spec 的价值在于强制在写代码之前澄清 |
| "Spec 会拖慢我们" | 15 分钟 spec 防止 15 小时返工 |
| "需求反正会变" | 那是为什么 spec 是 living document。过时的 spec 仍比没有 spec 好 |
| "用户知道他们想要什么" | 即使清晰的请求也有隐含假设。Spec 表面这些假设 |

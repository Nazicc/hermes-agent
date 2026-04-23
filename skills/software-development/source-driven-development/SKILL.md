---
name: source-driven-development
description: >
  Grounds every implementation decision in official documentation.
  Use when building with any framework or library where correctness matters.
  Use when you want authoritative, source-cited code free from outdated patterns.
trigger:
  - "use"
  - "official docs"
  - "check the documentation"
  - "what does the docs say"
  - "how do I use"
  - "official documentation"
  - "框架"
  - "官方文档"
  - "文档说"
  - "怎么用"
anti_trigger:
  - "pure logic"  # 纯逻辑不依赖框架
  - "simple renaming"  # 简单重命名不依赖文档
  - "I know this API by heart"  # 跳过文档验证
  - "just quickly"
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

**激活条件：** 构建涉及特定框架/库的代码、要求权威有据可查的实现、或要求"正确"实现。

**触发信号语言：**
- "use [framework]"、"official docs"、"check the documentation"
- "what does the docs say"、"how do I use"、"official documentation"
- "框架"、"官方文档"、"文档说"、"怎么用"
- 任何框架特定代码决策
- 构建 boilerplate、starter code 或会被复制到项目各处的模式

**区分相邻 skill：**
- `spec-driven-development`：spec 定义要构建什么，本 skill 定义如何根据官方文档正确构建
- `context-engineering`：加载上下文设置，本 skill 关注从源头验证框架特定决策

**Skip 场景：** 纯逻辑（不依赖框架版本）、简单重命名、用户明确说"快点就行"。

---

## R — 知识溯源 (Reading)

**核心原则：** Training data goes stale, APIs get deprecated, best practices evolve. 本 skill 确保每一个模式都能追溯到权威来源，用户可以验证。

**来源层级（按权威排序）：**

| 优先级 | 来源 | 示例 |
|--------|------|------|
| 1 | 官方文档 | react.dev, docs.djangoproject.com |
| 2 | 官方博客 / changelog | react.dev/blog, nextjs.org/blog |
| 3 | Web 标准参考 | MDN, web.dev, html.spec.whatwg.org |
| 4 | 浏览器/运行时兼容性 | caniuse.com, node.green |

**不是权威来源（不作为主要引用）：**
- Stack Overflow answers
- Blog posts or tutorials
- AI-generated documentation
- Training data

---

## I — 方法论骨架 (Interpretation)

**本 skill 的本质：** 每一个框架特定的代码决策都必须有官方文档背书。不是从记忆实现，而是验证、引用、让用户看到来源。

**为什么需要 source-driven？**
- Training data 包含过时模式，看起来正确但实际在新版本上 break
- 框架特定 API 记忆最不可靠
- 用户需要可以信任的代码，因为每个决策都能追溯到可检查的权威来源

**四步流程：**
```
DETECT ──→ FETCH ──→ IMPLEMENT ──→ CITE
  │          │           │            │
  ▼          ▼           ▼            ▼
 What       Get the    Follow the   Show your
 stack?    relevant   documented   sources
            docs       patterns
```

---

## A1 — 实践案例 (Past Application)

**反面教训：**
- **反面1：用记忆实现 API** → 函数签名在最新版本中变了，线上事故。Fetch docs 防止
- **反面2：用 Stack Overflow 作为权威来源** → 博客教程在 Stack Overflow 上看起来权威，但模式在当前版本已废弃
- **反面3：没检查版本** → React 18 的模式在 React 19 中不 work。检测版本是关键步骤

---

## E — 可执行步骤 (Execution) ★

### Step 1 — Detect Stack and Versions

从项目依赖文件读取确切的版本：

```bash
package.json      → Node/React/Vue/Angular
requirements.txt → Python/Django/Flask
go.mod           → Go
Cargo.toml       → Rust
Gemfile          → Ruby/Rails
```

明确说明找到的内容：

```
STACK DETECTED:
- React 19.1.0 (from package.json)
- Vite 6.2.0
- Tailwind CSS 4.0.3
→ Fetching official docs for the relevant patterns.
```

版本缺失或模糊？**问用户。** 不要猜——版本决定哪些模式是正确的。

### Step 2 — Fetch Official Documentation

获取功能对应的特定文档页面。不是首页，不是完整文档——是相关页面。

**来源层级（按权威排序）：**

| 优先级 | 来源 | 示例 |
|--------|------|------|
| 1 | 官方文档 | react.dev, docs.djangoproject.com |
| 2 | 官方博客 / changelog | react.dev/blog |
| 3 | Web 标准参考 | MDN, web.dev |
| 4 | 浏览器兼容性 | caniuse.com |

**精确获取：**

```
BAD:  Fetch the React homepage
GOOD: Fetch react.dev/reference/react/useActionState

BAD:  Search "django authentication best practices"
GOOD: Fetch docs.djangoproject.com/en/6.0/topics/auth/
```

官方来源冲突时（迁移指南 vs API 参考），向用户表面差异，并用检测到的版本验证哪个模式实际可用。

### Step 3 — Implement Following Documented Patterns

按照文档展示的模式写代码：

- 使用文档中的 API 签名，不是记忆
- 如果文档展示新方式，使用新方式
- 如果文档废弃某模式，不使用废弃版本
- 如果文档没有覆盖某内容，标记为未验证

**当文档与现有代码冲突时：**

```
CONFLICT DETECTED:
The existing codebase uses useState for form loading state,
but React 19 docs recommend useActionState for this pattern.
(Source: react.dev/reference/react/useActionState)

Options:
A) Use the modern pattern (useActionState) — consistent with current docs
B) Match existing code (useState) — consistent with codebase
→ Which approach do you prefer?
```

表面冲突。不要静默选一个。

### Step 4 — Cite Your Sources

每个框架特定模式都要有引用。用户必须能验证每个决策。

**在代码注释中：**

```typescript
// React 19 form handling with useActionState
// Source: https://react.dev/reference/react/useActionState#usage
const [state, formAction, isPending] = useActionState(submitOrder, initialState);
```

**在对话中：**

```
I'm using useActionState instead of manual useState for the
form submission state. React 19 replaced the manual
isPending/setIsPending pattern with this hook.

Source: https://react.dev/blog/2024/12/05/react-19#actions
"useTransition now supports async functions [...] to handle
pending states automatically"
```

**引用规则：**
- 完整 URL，不用短链接
- Deep links 带锚点优先（`/useActionState#usage` 优于 `/useActionState`）
- 引用支持非显而易见决策的相关段落
- 无法验证时明确说明：

```
UNVERIFIED: I could not find official documentation for this
pattern. This is based on training data and may be outdated.
Verify before using in production.
```

---

## B — 边界 (Boundary) ★

**反场景（NOT this skill）：**
- 正确性不依赖特定版本的场景（重命名变量、修复 typo）
- 纯逻辑，跨版本相同（循环、条件、数据结构）
- 用户明确要速度不要验证（"just do it quickly"）

**邻近方法论区分：**
- **本 skill vs context-engineering**：context-engineering 优化上下文设置，本 skill 验证框架特定决策的来源
- **本 skill vs spec-driven-development**：spec 定义构建什么，本 skill 验证如何正确构建

**已知失败模式：**
- 用"I believe"而非引用来源
- 实现模式不知道适用于哪个版本
- 引用 Stack Overflow 或 blog 作为主要来源
- 使用因训练数据看起来正确但实际已废弃的 API
- 在读取 package.json 前就实现

---

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "我对这个 API 很有信心" | 信心不是证据。Fetch 防止 hours of rework |
| "Fetch 文档浪费 tokens" | 幻觉一个 API 浪费更多 |
| "文档不会有我要的东西" | 如果文档没覆盖，这也是有价值的信息 |
| "简单任务不需要检查" | 简单任务中的错误模式会成为 template，被复制十次 |

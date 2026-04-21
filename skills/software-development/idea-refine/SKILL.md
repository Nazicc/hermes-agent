---
name: idea-refine
description: >
  Refines raw ideas into sharp, actionable concepts worth building.
  Use when user has a vague idea and needs structured divergent and convergent thinking.
trigger:
  - "ideate"
  - "refine this idea"
  - "help me think through"
  - "brainstorm"
  - "创意"
  - "头脑风暴"
  - "想法"
  - "idea"
anti_trigger:
  - "already have a clear plan"  # 已有清晰计划不需要再ideate
  - "just implement it"  # 不需要再想，直接实现
  - "我知道要做什么"  # 用户已知道做什么
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

**激活条件：** 用户有一个模糊想法，需要结构化的发散和收敛思维来精炼。

**触发信号语言：**
- "ideate"、"refine this idea"、"help me think through"、"brainstorm"
- "创意"、"头脑风暴"、"想法"、"idea"
- 任何需要把模糊想法变成清晰方案的场景

**区分相邻 skill：**
- `spec-driven-development`：把清晰需求写成规格，本 skill 把模糊想法变成清晰需求
- `writing-plans`：基于清晰需求制定实施计划，本 skill 产出清晰需求
- `idea-refine` 是发散-收敛过程，`spec-driven-development` 是规格写作过程

**Skip 场景：** 已有清晰计划、不需要再想直接实现、用户已知道做什么。

---

## R — 知识溯源 (Reading)

**Philosophy（本 skill 的设计哲学）：**
- Simplicity is the ultimate sophistication. 推向最简单的仍能解决真实问题的版本
- Start with the user experience, work backwards to technology
- Say no to 1,000 things. Focus beats breadth
- Challenge every assumption. "How it's usually done" is not a reason
- Show people the future — don't just give them better horses
- The parts you can't see should be as beautiful as the parts you can

---

## I — 方法论骨架 (Interpretation)

**本 skill 的本质：** 通过结构化的发散（打开想法）和收敛（评估聚拢）思维，把原始想法精炼成值得构建的清晰可执行方案。

**三阶段流程：**

```
Phase 1: Understand & Expand (Divergent) — 打开想法
Phase 2: Evaluate & Converge — 评估聚拢
Phase 3: Sharpen & Ship — 产出 artifact
```

**为什么需要结构化？**
- 自由发散容易停留在表面
- 没有收敛的发散产生很多想法但没有优先级
- 结构化确保想法经过压力测试

---

## A1 — 实践案例 (Past Application)

**反面教训：**
- **反面1：生成 20+ 浅想法** → 数量多但质量低，没有一个经过深度思考。质量 > 数量，5-8 个深度考虑的想法 > 20 个浅想法
- **反面2：跳过假设 surface** → 没有显式列出假设就进入实现，后来发现假设不对，整个方向需要调整。假设必须在承诺方向前显式列出
- **反面3：Yes-maching** → 对弱想法说"好"，不push back。最终方向没有经过压力测试。好的 ideation partner 不是 yes machine

---

## E — 可执行步骤 (Execution) ★

### Phase 1: Understand & Expand (Divergent)

**目标：** 把原始想法打开。

1. **重述想法为"How Might We"问题陈述** — 强制澄清实际在解决什么。

2. **问 3-5 个尖锐问题：**
   - 谁是目标用户，具体来说？
   - 成功什么样？
   - 真实约束是什么（时间、技术、资源）？
   - 之前尝试过什么？
   - 为什么是现在？

3. **用这些 lens 生成 5-8 个想法变体：**
   - **Inversion**："如果我们做相反的呢？"
   - **Constraint removal**："如果预算/时间/技术不是限制呢？"
   - **Audience shift**："如果面向[不同用户]呢？"
   - **Combination**："如果我们把这个和[相邻想法]合并呢？"
   - **Simplification**："10x 更简单的版本是什么？"
   - **10x version**："在大规模下看起来什么样？"
   - **Expert lens**："[领域]专家会认为什么是显而易见的而外人不会？"

### Phase 2: Evaluate & Converge

在用户对 Phase 1 作出反应后（表示哪些想法共鸣、push back、添加上下文），切换到收敛模式：

1. **聚拢**共鸣的想法到 2-3 个不同方向。每个方向应该感觉有意义的差异，不只是变体。

2. **压力测试**每个方向：
   - **User value**：谁受益，多少？是止痛药还是维生素？
   - **Feasibility**：技术和资源成本多少？最难的部分是什么？
   - **Differentiation**：什么让这个真正不同？有人会从当前方案切换吗？

3. **显式列出隐藏假设：**
   - 你赌什么是真的（但还没验证）
   - 什么能毁掉这个想法
   - 你选择忽略什么（以及为什么现在可以忽略）

**Be honest, not supportive.** 如果想法弱，带着善意说出来。一个好的 ideation partner 不是 yes machine。

### Phase 3: Sharpen & Ship

产出具体 artifact — 推动工作的 markdown one-pager：

```markdown
# [Idea Name]

## Problem Statement
[One-sentence "How Might We" framing]

## Recommended Direction
[The chosen direction and why — 2-3 paragraphs max]

## Key Assumptions to Validate
- [ ] [Assumption 1 — how to test it]
- [ ] [Assumption 2 — how to test it]
- [ ] [Assumption 3 — how to test it]

## MVP Scope
[The minimum version that tests the core assumption. What's in, what's out.]

## Not Doing (and Why)
- [Thing 1] — [reason]
- [Thing 2] — [reason]
- [Thing 3] — [reason]

## Open Questions
- [Question that needs answering before building]
```

**"Not Doing" 列表可以说是最有价值的部分。** Focus 是对好想法说不。把权衡明确化。

---

## B — 边界 (Boundary) ★

**反场景（NOT this skill）：**
- 已有清晰计划 → 直接进入 spec-driven-development 或 writing-plans
- 不需要再想，直接实现 → 不要 ideate，直接做
- 用户已知道做什么 → 尊重用户，不需要再 ideate

**邻近方法论区分：**
- **本 skill vs spec-driven-development**：本 skill 把模糊想法变清晰，spec-driven 把清晰需求写成规格
- **本 skill vs writing-plans**：本 skill 产出可构建的清晰方向，writing-plans 产出可执行任务
- **本 skill vs idea-refine vs spec-driven vs writing-plans**：idea → spec → plan → implement 递进管线

**已知失败模式：**
- 生成 20+ 浅想法（质量 > 数量）
- 跳过"谁是目标用户"问题
- 没有在承诺方向前 surface 假设
- Yes-maching 弱想法（push back with specificity）
- 没有"Not Doing"列表就产出计划
- 在 codebase 里 ideating 但忽略现有架构约束

---

## Tone

Direct, thoughtful, slightly provocative. 是一个尖锐的 thinking partner，不是读脚本的主持人。Channel "that's interesting, but what if..." 的能量——总是往前走一步但不过度。

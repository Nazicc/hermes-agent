# cangjie-skill × Hermes Skills 融合报告

**日期:** 2026-04-22
**来源:** [kangarooking/cangjie-skill](https://github.com/kangarooking/cangjie-skill) (444 ⭐, AGPL-3.0)

---

## 一、cangjie-skill 核心创新：RIA-TV++ 结构

现有 Hermes skills 是**给人类读者看的手册**。cangjie-skill 是**给 agent 执行者看的可执行工具**。

关键差异：

| 维度 | 现有 Hermes Skill | cangjie-skill SKILL.md |
|------|-------------------|----------------------|
| 激活判断 | `description` 泛泛描述 | **A2 trigger 信号 + 语言信号** |
| 使用步骤 | 散落在文字描述中 | **E (Execution) 1-2-3 可执行步骤** |
| 失败模式 | 无 | **B (Boundary) 反场景 + 诱饵测试** |
| 知识溯源 | 无 | **R 原文引用 + A1 书中案例** |
| 可进化性 | 无 | **test-prompts.json 压力测试** |

---

## 二、融合：Hermes Skill RIA-TV++ 升级格式

### 2.1 升级后的 SKILL.md 模板（RIA-TV++ 版）

```markdown
---
name: {{skill-name}}
description: |
  {{A2 Trigger: 何时调用 + 何时不调用 + 语言信号, ≤300字}}
  触发信号示例:
  - 用户说"帮我debug..." → 激活 systematic-debugging
  - 用户说"实现XX功能" → 激活 test-driven-development
  - 不适用于: 纯信息查询、日常闲聊
trigger:
  - "debug"
  - "出错了"
  - "跑不通"
  - "为什么XX不工作"
anti_trigger:
  - "只是问问"
  - "给我讲讲"
  - 纯信息查询场景
source: hermes-agent / {{external_source}}
author: Hermes Agent
license: MIT
version: 1.0.0
metadata:
  hermes:
    tags: [{{tag1}}, {{tag2}}]
    related_skills: [{{skill-a}}, {{skill-b}}]
    quality_redlines:
      - MUST have E (Execution) section with numbered steps
      - MUST have B (Boundary) section with anti-triggers
      - MUST have A2 (Trigger) section with language signals
      - description MUST NOT be a generic phrase like "一个关于X的skill"
---

# {{Skill Title}}

## A2 — 触发场景 (Trigger) ★

### 何时激活此 skill

用户在以下情境时会需要这个 skill：

1. **{{场景1}}** — {{具体描述}}
2. **{{场景2}}** — {{具体描述}}
3. **{{场景3}}** — {{具体描述}}

### 语言信号（用户话里出现这些就应激活）

- "{{典型措辞1}}"
- "{{典型措辞2}}"
- "{{典型措辞3}}"

### 相邻 skill 的区分

- 与 `{{related-skill-a}}` 的区别: {{...}}
- 与 `{{related-skill-b}}` 的区别: {{...}}

---

## R — 知识溯源 (Reading)

> {{原文引用/权威来源, ≤150字, 必须标注来源}}
> — {{SOURCE}}, {{CHAPTER/SECTION}}

---

## I — 方法论骨架 (Interpretation)

{{用自己的话重写这个方法论, 5-15行。
读完这段, 一个没读过原始资料的人应当能理解这个方法论在做什么。
禁止照搬原文, 禁止堆砌修辞。}}

---

## A1 — 实践案例 (Past Application)

### 案例: {{案例名}}

- **问题**: {{遇到了什么}}
- **方法论的使用**: {{怎么用这个方法论思考/处理}}
- **结论**: {{得出了什么}}
- **结果**: {{实际发生了什么}}

---

## E — 可执行步骤 (Execution) ★

当 skill 被激活后, agent 按以下步骤执行:

1. **{{步骤1}}**
   - 完成标准: {{如何判断这一步已完成}}
   - 判停条件: 若 {{X}} 则跳到步骤 {{N}}

2. **{{步骤2}}**
   - 完成标准: {{...}}
   - 判停条件: 若 {{X}} 则停止并报告

3. **{{步骤3}}**
   - 完成标准: {{...}}

---

## B — 边界 (Boundary) ★

### 不要在以下情况使用此 skill

- **{{反场景1}}** — {{为什么不适用}}
- **{{反场景2}}** — {{为什么不适用}}
- **{{反场景3}}** — {{为什么不适用}}

### 容易混淆的邻近方法论

- `{{nearby-skill}}` — {{如何区分}}
- `{{nearby-skill}}` — {{如何区分}}

### 已知失败模式

- {{来自实际踩坑记录}}
- {{来自社区报告}}

---

## 质量红线 (违反则阻止输出)

1. `description` 不能只是"一个关于X的skill" — 必须有 trigger 信号
2. 必须有 **E (Execution)** 段 — 带完成标准和判停条件
3. 必须有 **B (Boundary)** 段 — 含 anti-trigger 反场景
4. 必须有 **A2 (Trigger)** 段 — 含语言信号
5. 相关 skills 必须填写 `related_skills` 字段

---

## 测试用例 (压力测试)

### 应激活（正确调用）

- "{{test_prompt_1}}"
- "{{test_prompt_2}}"

### 不应激活（诱饵题 — agent 不应调用此 skill）

- "{{distractor_prompt_1}}"
- "{{distractor_prompt_2}}"

### 边界模糊（需要判断）

- "{{edge_case_prompt}}"

---
```

---

## 三、现有 Hermes Skills 差距分析

| Skill | A2 Trigger | E Execution | B Boundary | test-prompts | 差距评分 |
|-------|-----------|------------|-----------|-------------|---------|
| systematic-debugging | 部分 | 部分 | 部分 | 无 | 65% |
| test-driven-development | 部分 | 部分 | 无 | 无 | 55% |
| planning-and-task-breakdown | 部分 | 部分 | 无 | 无 | 50% |
| code-review-and-quality | 部分 | 部分 | 部分 | 无 | 60% |
| incremental-implementation | 部分 | 部分 | 无 | 无 | 50% |
| systematic-debugging | 部分 | 部分 | 部分 | 无 | 65% |

**平均差距:** ~55-65%，主要缺 A2 trigger 细粒度和 B boundary 反场景。

---

## 四、融合行动计划

### 第一批（已完成 ✅）

1. **systematic-debugging** ✅ — 2026-04-22 完成
   - 已有完整内容，缺 A2 + 诱饵测试
   - 升级：添加 A2 trigger + E execution + B boundary + R/I/A1

2. **test-driven-development** ✅ — 2026-04-22 完成
   - 升级：添加 A2 trigger + E execution + B boundary + R/I/A1
   - 升级后文件大小：约 500 行（+158 行新内容）

3. **planning-and-task-breakdown** ✅ — 2026-04-22 完成
   - 升级：添加 A2 trigger + E execution + B boundary + R/I/A1
   - 升级后文件大小：约 377 行（+155 行新内容）

### 第二批（待办）

4. **requesting-code-review** — 高频使用，ROI 高
5. **incremental-implementation** — 高频使用
6. **code-simplification** — 重构相关

### 第三批

7. 其他 skills（按使用频率排序）

---

## 五、cangjie-skill 生态借鉴

```
nuwa-skill      ──→ 蒸馏人（思维方式、表达DNA）
cangjie-skill   ──→ 蒸馏书（方法论、框架、原则）
darwin-skill    ──→ 进化任意skill（自动压力测试+迭代）
```

Hermes 可借鉴的生态玩法：
- 把「网络安全行业知识」蒸馏成 RIA-TV++ skill pack（如渗透测试、红队演练、应急响应）
- 把「每日安全研究」定期用 darwin-skill 进化
- 与 nuwa-skill 互补：nuwa 蒸馏人，Hermes 蒸馏领域知识

---

## 六、参考资源

- 源项目: https://github.com/kangarooking/cangjie-skill
- book2skill 元 skill: https://github.com/kangarooking/cangjie-skill/blob/main/SKILL.md
- RIA-TV++ 方法论: https://github.com/kangarooking/cangjie-skill/blob/main/methodology/00-overview.md
- SKILL.md 模板: https://github.com/kangarooking/cangjie-skill/blob/main/templates/SKILL.md.template
- 生态项目:
  - nuwa-skill: https://github.com/alchaincyf/nuwa-skill
  - darwin-skill: https://github.com/alchaincyf/darwin-skill
- 已生成 skill packs:
  - buffett-letters-skill (巴菲特, 20 skills)
  - poor-charlies-almanack-skill (芒格, 12 skills)
  - huangdi-neijing-skill (黄帝内经, 22 skills)

---
name: hermes-eval
description: |
  Hermes Agent Skill Evaluation Harness — 自动化评测 skills 质量的框架。
  每个 skill 有独立 YAML suite，包含多维度测试用例（reasoning/command/file_edit）。
  接入 weekly cron 后，所有 skill 升级必须先 PASS harness，否则跳过升级。
  Trigger: 用户说"跑一下评测"、eval"、"测试skill"、或每周 cron 自动触发。
  Anti-trigger: 纯信息查询。
trigger:
  - "评测"
  - "eval"
  - "测试skill"
  - "跑一下测试"
  - "hermes-eval"
  - "质量"
anti_trigger:
  - "只是问问"
  - "怎么写"
version: 2.0.0
metadata:
  sources: []
  hermes:
    tags: [evaluation, testing, quality, benchmark, skill-assessment]
    related_skills: [skills-evolution-from-research, systematic-debugging, test-driven-development]
    quality_redlines:
      - MUST have R (Reference) section with RIA-TV++ format description
      - MUST have E (Execution) section with harness.py usage
      - MUST have A2 (Trigger) section with activation signals
      - MUST have B (Boundary) section with anti-triggers
      - harness.py MUST be runnable without API key (degrades gracefully)
---

# Hermes Eval — Skill Evaluation Harness

## A2 — 触发场景 (Trigger) ★

### 何时激活

1. **Cron 自动触发** — 每周 upgrade cron 运行 harness
2. **手动评测请求** — 用户说"跑一下评测"、hermes-eval、测试 skill
3. **Skill 升级前 gate** — 所有 v2.0.0 升级必须先 PASS harness

### 语言信号

- "评测"
- "eval"
- "测试 skill"
- "hermes-eval"
- "跑一下测试"
- "质量"

### Anti-Trigger（不应激活）

- 纯信息查询
- "只是问问"

---

## R — Reference（参考）

### 框架架构

```
hermes-eval/
├── SKILL.md              本文件
├── harness.py            评测引擎（核心）
└── suites/               测试用例集
    ├── systematic-debugging.yaml
    ├── test-driven-development.yaml
    ├── software-development/
    └── ...（按 skill 类别组织）
```

### 测试类型

| type | 执行方式 | 评测者 |
|------|---------|--------|
| `reasoning` | LLM 模拟 skill 执行 | MiniMax LLM Judge |
| `command` | 执行 shell 命令 | exit code + stdout |
| `file_edit` | 检查 SKILL.md 内容 | 关键词/结构匹配 |
| `output_match` | 匹配输出字符串 | 精确匹配 |

### 评分标准

- **PASS** — 达到预期
- **FAIL** — 未达预期（不应升级）
- **SKIP** — 无执行条件（无 API key / 文件不存在）

升级门禁：`score >= 0.8` 才允许升级 skill 到 v2.0.0

### 基线数据（2026-04-22）

| Skill | Score |
|-------|-------|
| idea-refine | 71% |
| spec-driven-development | 71% |
| hermes-agent-architecture | 67% |
| systematic-debugging | 62% |
| test-driven-development | 62% |
| ... | ... |
| **OVERALL** | **54.1%** |

---

## E — Execution（执行步骤）★

### 1. 列出所有 suites

```bash
python3 ~/.hermes/skills/software-development/hermes-eval/harness.py --list
```

### 2. 运行全套评测

```bash
python3 ~/.hermes/skills/software-development/hermes-eval/harness.py
```

### 3. 运行单个 skill 评测

```bash
python3 ~/.hermes/skills/software-development/hermes-eval/harness.py --skill systematic-debugging
```

### 4. 运行整个 suite

```bash
python3 ~/.hermes/skills/software-development/hermes-eval/harness.py --suite software-development
```

### 5. 输出格式

stdout 输出表格：

```
Skill                          Ver        Pass  Fail  Skip  Score    Time
----------------------------------------------------------------------------
systematic-debugging           2.0.0         5     0     3  ██████░░░  2ms
test-driven-development        2.0.0         5     0     3  ██████░░░  1ms
------------------------------------------------------------------------------
OVERALL                                                   54.1%
```

详细 JSON 结果保存在 `results/YYYYMMDD-HHMMSS_{skill}.json`

### 6. 解读结果

| Score 区间 | 行动 |
|-----------|------|
| >= 80% | ✅ PASS — 可升级 |
| 50%–79% | ⚠️ WARN — 审查后升级 |
| < 50% | ❌ FAIL — 跳过升级 |

### 7. 接入 weekly cron（升级门禁逻辑）

```bash
# 在 hermes-weekly-upgrade cron 里，eval 阶段：
cd ~/.hermes/skills/software-development/hermes-eval
result=$(python3 harness.py --skill $SKILL_NAME 2>&1)
score=$(echo "$result" | grep OVERALL | awk '{print $NF}' | tr -d '%')

if (( $(echo "$score >= 80" | bc -l) )); then
  echo "PASS: $SKILL_NAME at $score%"
  # 执行升级
else
  echo "SKIP: $SKILL_NAME below 80% threshold"
fi
```

---

## B — Boundary（边界条件）

### 限制

- **无 API key**：reasoning 测试降级为 SKIP（file_edit 仍正常运行）
- **Suite 不存在**：跳过并警告，不阻塞其他 suite
- **文件权限错误**：跳过并报告，不影响其他 skill
- **执行超时**：60s 硬限制，超时计为 FAIL

### 安全边界

- harness **不修改** `~/.hermes/hermes-agent/skills/`（git 目录）
- 仅写入 `~/.hermes/skills/`（runtime 目录）
- 不执行任何 `rm -rf`、网络扫描等危险操作
- 不推送任何数据到外部（除 LLM Judge 调用）

### 已知限制

- reasoning 测试依赖 MiniMax API，无 key 时跳过
- 当前 keyword 匹配较粗放，未来可升级为 embedding similarity

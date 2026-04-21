# llm-wiki-agent 安装测试报告

**日期:** 2026-04-21
**项目:** github.com/SamurAIGPT/llm-wiki-agent
**安装路径:** ~/llm-wiki-agent/

---

## 安装方式结论

**最优方式: 零依赖，Agent 驱动模式**

```bash
git clone https://github.com/SamurAIGPT/llm-wiki-agent.git ~/llm-wiki-agent
```

不需要 pip install，不需要配置环境变量。Agent（Claude Code / Codex / OpenCode）直接读取 CLAUDE.md / AGENTS.md 即可通过自然语言使用所有功能。

---

## 环境配置（MiniMax Token Plan）

| Env Var | 值 |
|---------|-----|
| `OPENAI_API_KEY` | `sk-cp-REAL_KEY_WAS_HEREGl1yRSGlF16E8zlQBuUV1fPKAMWzLxQMnoc1r4jhTP-5ZANOcZQIXVzlRXNkmCSxUj2r-8Q4CAQtec5ST7u5U` |
| `LITELLM_API_KEY` | 同上 |
| `LLM_MODEL` | `MiniMax-M2.7` |
| `LLM_MODEL_FAST` | `MiniMax-M2.7` |
| `LLM_BASE_URL` | `https://api.minimaxi.com/v1` |

**关键发现:** litellm 1.x 不认识 "MiniMax-M2.7" 模型名，直接使用会报
`LLM Provider NOT provided`。必须设置 `custom_llm_provider='openai'` + `api_base`。

---

## 测试结果

### 1. health.py ✅
- 依赖: 纯标准库（stdlib only）
- 结果: 结构检查通过，零问题
- 命令: `cd ~/llm-wiki-agent && ./run_minimax.sh python3 tools/health.py --json`

### 2. heal.py ✅
- 依赖: 纯标准库
- 结果: 图谱自愈检查通过
- 命令: `cd ~/llm-wiki-agent && PYTHONPATH=. python3 tools/heal.py`

### 3. ingest.py ✅
- 依赖: litellm>=1.0.0
- 结果: 文档成功摄取，创建 wiki/sources/, wiki/entities/, 更新 index.md/overview.md/log.md
- 命令: `cd ~/llm-wiki-agent && ./run_minimax.sh python3 tools/ingest.py raw/myfile.md`

### 4. query.py ✅
- 依赖: litellm>=1.0.0
- 结果: 语义合成回答成功，引用 [[wikilinks]]
- 命令: `cd ~/llm-wiki-agent && ./run_minimax.sh python3 tools/query.py "question?"`

### 5. lint.py ✅
- 依赖: litellm>=1.0.0
- 结果: 语义检查报告生成成功（含矛盾检测、数据缺口分析）
- 命令: `cd ~/llm-wiki-agent && ./run_minimax.sh python3 tools/lint.py`

### 6. build_graph.py ✅
- 依赖: networkx（可选）
- 结果: graph.json + graph.html 生成成功
- 命令: `cd ~/llm-wiki-agent && ./run_minimax.sh python3 tools/build_graph.py`

---

## 已应用的关键 Patch

所有 4 个 litellm 工具的 `call_llm()` 函数已添加 MiniMax Token Plan 兼容代码:

```python
api_base = os.getenv("LLM_BASE_URL", "")

kwargs = {
    "model": model,
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": max_tokens
}

# MiniMax Token Plan: use openai provider with custom api_base
if api_base and model == "MiniMax-M2.7":
    kwargs["custom_llm_provider"] = "openai"
    kwargs["api_base"] = api_base

response = completion(**kwargs)
```

Patch 应用于:
- `~/llm-wiki-agent/tools/ingest.py`
- `~/llm-wiki-agent/tools/query.py`
- `~/llm-wiki-agent/tools/lint.py`
- `~/llm-wiki-agent/tools/build_graph.py`

---

## 交付物

| 文件 | 说明 |
|------|------|
| `~/llm-wiki-agent/` | 完整安装（含 patch） |
| `~/llm-wiki-agent/.env.minimax` | MiniMax Token Plan 标准配置 |
| `~/llm-wiki-agent/run_minimax.sh` | 启动脚本，自动加载 env 并执行命令 |
| `~/.hermes/skills/productivity/llm-wiki-agent/SKILL.md` | Skill 参考文档 |
| 本文件 | 测试报告 |

---

## 与 MemPalace / Sirchmunk 的定位差异

| 系统 | 模式 | 核心特点 |
|------|------|---------|
| MemPalace | 语义记忆 + RAG | ONNX embeddings, ChromaDB, MCP 29 tools |
| Sirchmunk | embedding-free 全文检索 | ripgrep + LLM, DuckDB, self-evolving |
| **llm-wiki-agent** | **预综合维基** | Agent 驱动, 零基础设施, 文档→结构化维基 |

llm-wiki-agent 负责**预综合**（文档→维基），MemPalace/Sirchmunk 负责**查询时检索**，三者互补。

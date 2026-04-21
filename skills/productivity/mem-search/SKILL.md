---
name: mem-search
description: >
  Three-layer memory search protocol for SimpleMem/MemPalace.
  Step 1: search index → Step 2: timeline context → Step 3: fetch full entries.
  Inspired by claude-mem's mem-search skill (65k stars).
  Saves 10x tokens by filtering before fetching full details.
triggers:
  - "search memory"
  - "query memories"
  - "find in past sessions"
  - "did we already solve this"
  - "how did we do X last time"
  - "search SimpleMem"
  - "memory search"
---

# Memory Search — Three-Layer Protocol

> 引用自 claude-mem `mem-search` skill 设计。节省 10x tokens。

## 适用场景

用户问及**历史会话**（非当前对话）：
- "上次这个 bug 是怎么修的？"
- "之前我们做过这个功能吗？"
- "上周发生了什么？"

## 三层工作流

**核心原则：永远先过滤，再取详情。**

---

### Step 1: Search — 获取索引

```python
from main import SimpleMemSystem
system = SimpleMemSystem()

# 语义搜索（类似 lucene 的词项权重）
results = system.ask("你的查询")
# 返回: 自然语言回答（融合了相关记忆）
```

**对于 MemPalace：**
```bash
mempalace search "authentication bug fix" --top-k 20
```

---

### Step 2: Timeline — 获取上下文

通过 Step 1 发现的相关记忆 ID，围绕锚点展开时间上下文：

```python
# SimpleMem 不内置 timeline，依赖 ask() 的混合检索
# 返回结果已包含 semantic + keyword + structured 三路召回
answer = system.ask("authentication bug fix")
print(answer)
```

**MemPalace 方式：**
```bash
mempalace mine --dry-run  # 扫描当前项目上下文
```

---

### Step 3: Fetch — 取完整条目

验证后对感兴趣的记忆 ID 取完整详情：

```python
# SimpleMem
all_memories = system.get_all_memories()
for m in all_memories:
    if relevant_to_query(m):
        print(f"ID: {m.entry_id}")
        print(f"记忆: {m.lossless_restatement}")
        print(f"关键词: {m.keywords}")
        print(f"主题: {m.topic}")
```

---

## Token 节省原理

| 阶段 | 每条 token |
|------|-----------|
| Search index | ~50-100 |
| Timeline context | ~100-200 |
| Full entry | ~500-1000 |

**直接全量 fetch = 浪费 10x tokens。**

---

## 与 claude-mem mem-search 的对比

| 维度 | claude-mem | SimpleMem | MemPalace |
|------|-----------|-----------|-----------|
| Search | MCP `search()` API | `ask()` 语义回答 | `mempalace search` |
| Timeline | `timeline()` API | 隐式（ask 内部） | 无 |
| Fetch | `get_observations()` | `get_all_memories()` | 直接读取 DB |
| 存储 | SQLite + Chroma | LanceDB | ChromaDB |
| 隐私标签 | `<private>` | `<private>` ✅已集成 | 无 |

---

## 快速命令

```bash
# SimpleMem 快速搜索
cd ~/SimpleMem && .venv/bin/python -c "
import sys; sys.path.insert(0, '.')
from main import SimpleMemSystem
system = SimpleMemSystem()
print(system.ask('你的查询'))
"

# MemPalace 搜索
mempalace search "你的查询" --top-k 10

# Sirchmunk 搜索（需要 LLM）
curl -s "http://localhost:8584/api/v1/search?query=你的查询"
```

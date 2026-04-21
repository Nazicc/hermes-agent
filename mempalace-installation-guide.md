# MemPalace 安装配置完整指南

> 本指南基于 v3.3.2，针对 macOS/Linux 环境深度优化，涵盖最小化安装、MCP 集成、Claude Code Hooks、记忆层接入四大路径。
> 目标：**零阻断、零 API key、零云依赖**，让 MemPalace 无缝融入 Hermes Agent 工作流。

---

## 目录

1. [核心概念速查](#1-核心概念速查)
2. [安装前检查清单](#2-安装前检查清单)
3. [最小化安装（推荐）](#3-最小化安装推荐)
4. [开发模式安装](#4-开发模式安装)
5. [初始化与首次配置](#5-初始化与首次配置)
6. [MCP Server 接入（推荐）](#6-mcp-server-接入推荐)
7. [Claude Code Hooks 自动保存](#7-claude-code-hooks-自动保存)
8. [Hermes Agent 记忆层集成](#8-hermes-agent-记忆层集成)
9. [验证安装成功](#9-验证安装成功)
10. [卸载与数据迁移](#10-卸载与数据迁移)

---

## 1. 核心概念速查

| 概念 | 含义 | 类比 |
|------|------|------|
| **Wing** | 宽泛类别（人/项目/主题） | 宫殿侧翼 |
| **Room** | 时间或主题分组（天/会话） | 房间 |
| **Drawer** | 完整逐字内容 | 抽屉 |
| **AAAK** | Agent Accessible Abstract Knowledge，LLM 可扫描的压缩索引 | 索引卡 |
| **Closet** | LLM 专用压缩总结（ closets 是 LLM 的私有记忆空间） | 储物间 |
| **Diary** | 每日会话摘要 | 日记 |

> **设计原则**：Never summarize（不摘要原文）、append-only（增量追加）、entity-first（实体优先）

---

## 2. 安装前检查清单

```bash
# 检查 Python 版本（要求 3.9+）
python3 --version   # → Python 3.9.x / 3.10+ 均可

# 检查 pip/uv
which pip pipx uv 2>/dev/null

# 检查磁盘空间（需要 ~300MB 默认 embedding 模型）
df -h ~

# 检查是否有 GPU（可选，加速 embedding）
python3 -c "import torch; print('CUDA:', torch.cuda.is_available())" 2>/dev/null || echo "CPU mode OK"

# 检查 ~/.mempalace 是否已存在（避免重复初始化）
ls ~/.mempalace 2>/dev/null && echo "WARNING: 已存在配置" || echo "干净状态"
```

---

## 3. 最小化安装（推荐）

### 3.1 推荐方式：uv（最快）

```bash
# 安装 uv（如果没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 全局安装 mempalace CLI
uv tool install mempalace

# 验证安装
mempalace --version
# → mempalace 3.3.2

# 安装默认依赖（ChromaDB + embedding 模型）
# uv tool 会自动处理依赖，但推荐显式安装 chromadb
uv pip install chromadb --system
```

### 3.2 备选方式：pipx（隔离环境）

```bash
# 安装（隔离，避免依赖冲突）
pipx install mempalace

# 或指定版本
pipx install mempalace==3.3.2
```

### 3.3 备选方式：pip（系统级）

```bash
pip install mempalace

# 验证
mempalace --version
mempalace --help
```

---

## 4. 开发模式安装

适用于需要修改源码、贡献 PR、或深度定制的用户。

```bash
# 克隆仓库（使用 develop 分支获取最新功能）
git clone https://github.com/MemPalace/mempalace.git
cd mempalace

# 方式 A：uv 安装（推荐）
uv sync                  # 创建 .venv 并安装所有依赖
uv sync --dev            # 包含开发依赖（pytest, ruff）

# 方式 B：pip 安装
pip install -e ".[dev]"

# 验证开发环境
python -m pytest tests/ -v --ignore=tests/benchmarks --co -q | head -20
ruff check .
ruff format --check .
```

### 依赖说明（来自 pyproject.toml）

| 依赖组 | 核心依赖 | 说明 |
|--------|----------|------|
| **核心** | chromadb, httpx, attrs | 向量存储 + HTTP 客户端 |
| **CLI** | typer, rich | 命令行界面 |
| **Mining** | anthropic（可选） | 对话挖掘用 LLM |
| **Embedding** | sentence-transformers | 本地 embedding 模型（~300MB） |
| **Dev** | pytest, pytest-cov, ruff | 测试 + 代码规范 |

---

## 5. 初始化与首次配置

### 5.1 交互式初始化（推荐首次）

```bash
mempalace init ~/palace
# 或不指定路径（默认 ~/.mempalace/palace）
mempalace init
```

`init` 会启动交互式引导：
- 选择 embedding 模型（默认：sentence-transformers/all-MiniLM-L6-v2）
- 设置默认 backend（默认：chroma）
- 可选：配置 LLM provider（用于 diary 生成等高级功能）

### 5.2 手动初始化（自动化场景）

```bash
# 创建 palace 目录
mkdir -p ~/palace

# 初始化配置
mempalace init ~/palace --no-interactive

# 验证目录结构
ls -la ~/palace/
# ├── .mempalace/          # 内部数据
# ├── palace/             # 记忆存储
# └── config.yaml         # 配置文件
```

### 5.3 配置文件结构

```yaml
# ~/.mempalace/config.yaml（或项目内 .mempalace/config.yaml）
palace:
  path: ~/palace                    # palace 根目录
  backend: chroma                   # 可替换为其他 backend
  embedding:
    provider: sentence-transformers
    model: all-MiniLM-L6-v2         # 默认轻量模型
    # model: all-mpnet-base-v2     # 高精度选项（更慢）
    device: cpu                     # cpu / cuda

llm:
  provider: anthropic               # 用于 diary 生成、entity 检测
  model: claude-sonnet-4-7         # 可选
  # 设为空则只用本地模型，不调用 API

hooks:
  save_interval: 15                 # 每 N 条人类消息触发一次保存
  verbose: false                    # true = 在 chat 中显示保存内容

mcp:
  enabled: true
  port: 8765                        # MCP server 端口
```

---

## 6. MCP Server 接入（推荐）

MCP Server 提供 29 个工具，是 Hermes Agent 接入 MemPalace 的**最佳路径**。

### 6.1 启动 MCP Server

```bash
# 方式 A：独立进程（长期运行）
mempalace mcp --port 8765 &
# 后台运行，可加入 launchd/systemd 管理

# 方式 B：stdio 模式（按需启动）
mempalace mcp --stdio
# 输出 JSON-RPC 格式，用于 MCP 客户端

# 方式 C：检查 MCP 配置
mempalace mcp --check
```

### 6.2 MCP 工具清单（29 个核心工具）

#### Palace 操作
| 工具 | 描述 |
|------|------|
| `mempalace_create_wing` | 创建新的 wing（人/项目） |
| `mempalace_create_room` | 在 wing 内创建 room |
| `mempalace_add_drawer` | 添加逐字内容到 drawer |
| `mempalace_search` | 语义搜索 palace |
| `mempalace_wake_up` | 加载上下文用于新会话 |

#### 知识图谱操作
| 工具 | 描述 |
|------|------|
| `mempalace_kg_add` | 添加实体关系（三元组） |
| `mempalace_kg_query` | 查询实体关系 |
| `mempalace_kg_invalidate` | 使过期关系失效 |
| `mempalace_kg_timeline` | 时间线查询 |

#### Agent 相关
| 工具 | 描述 |
|------|------|
| `mempalace_list_agents` | 列出所有 agent 的 wing |
| `mempalace_agent_diary` | 读写 agent 日记 |

### 6.3 Hermes Agent MCP 配置

在 `~/.hermes/config.yaml` 中添加：

```yaml
mcp:
  servers:
    mempalace:
      type: stdio
      command: "mempalace"
      args: ["mcp", "--stdio"]
      env:
        MEMPALACE_PATH: ~/palace      # 指向你的 palace 目录
```

> **注意**：Hermes Agent 使用内置 MCP 客户端，配置路径可能因版本而异，请参考 `mcp: native-mcp` skill。

---

## 7. Claude Code Hooks 自动保存

Claude Code 是目前最流行的 AI coding agent，MemPalace 提供了原生 hooks 实现会话自动保存。

### 7.1 下载 Hook 脚本

```bash
# 从 GitHub 直接下载（不需要完整 clone）
HOOKS_DIR="$HOME/.mempalace/hooks"
mkdir -p "$HOOKS_DIR"

curl -s https://raw.githubusercontent.com/MemPalace/mempalace/main/hooks/mempal_save_hook.sh \
  -o "$HOOKS_DIR/mempal_save_hook.sh"
curl -s https://raw.githubusercontent.com/MemPalace/mempalace/main/hooks/mempal_precompact_hook.sh \
  -o "$HOOKS_DIR/mempal_precompact_hook.sh"

chmod +x "$HOOKS_DIR/mempal_save_hook.sh" "$HOOKS_DIR/mempal_precompact_hook.sh"
```

### 7.2 配置 Claude Code Hooks

编辑 `~/.claude/settings.local.json`（或项目内 `.claude/settings.local.json`）：

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "/Users/can/.mempalace/hooks/mempal_save_hook.sh",
        "timeout": 30
      }]
    }],
    "PreCompact": [{
      "hooks": [{
        "type": "command",
        "command": "/Users/can/.mempalace/hooks/mempal_precompact_hook.sh",
        "timeout": 30
      }]
    }]
  }
}
```

### 7.3 配置参数

在 `mempal_save_hook.sh` 顶部调整：

```bash
SAVE_INTERVAL=15        # 每 N 条人类消息保存一次（默认 15）
STATE_DIR="$HOME/.mempalace/hook_state"
MEMPAL_DIR=""           # 可选：自动 mine 的目录路径
MEMPAL_VERBOSE=false    # true = 在 chat 中显示保存内容（开发调试用）
MEMPAL_PYTHON="/usr/bin/python3"  # Python 解释器路径（macOS GUI 用户需设置）
```

### 7.4 调试 Hook

```bash
# 查看 hook 日志
cat ~/.mempalace/hook_state/hook.log

# 示例输出：
# [14:30:15] Session abc123: 12 exchanges, 12 since last save
# [14:35:22] Session abc123: 15 exchanges, 15 since last save
# [14:35:22] TRIGGERING SAVE at exchange 15
```

> **macOS 用户注意**：如果 Claude Code 通过 GUI（Spotlight/Dock）启动，`PATH` 不包含用户 shell 配置的路径，需要设置 `MEMPAL_PYTHON` 为系统 Python 路径。

---

## 8. Hermes Agent 记忆层集成

MemPalace 的 Wing/Room/Drawer 结构天然适合作为 Hermes Agent 的**长期记忆基础设施**，提供会话间的上下文连续性。

### 8.1 架构设计

```
┌─────────────────────────────────────────────────────┐
│              Hermes Agent Session                   │
│  (短期记忆：当前会话上下文)                           │
└──────────────────┬──────────────────────────────────┘
                   │ session_end
                   ▼
┌─────────────────────────────────────────────────────┐
│           MemPalace Palace (长期记忆)                │
│                                                   │
│  Wing: user-profile                               │
│    Room: 2026-04-21                               │
│      Drawer: "用户偏好 Python，习惯用 ruff..."      │
│                                                   │
│  Wing: projects/hermes-agent                      │
│    Room: sessions                                 │
│      Drawer: (逐字会话记录)                        │
│                                                   │
│  Wing: knowledge-graph                            │
│    Room: entities                                 │
│      (时序实体关系)                                │
└──────────────────┬──────────────────────────────────┘
                   │ wake-up
                   ▼
┌─────────────────────────────────────────────────────┐
│         Next Hermes Agent Session                    │
│  (通过 mempalace wake-up 加载历史上下文)             │
└─────────────────────────────────────────────────────┘
```

### 8.2 接入步骤

**Step 1：安装并初始化（已完成 Section 3-5）**

**Step 2：配置 MCP Server（已完成 Section 6）**

**Step 3：创建记忆结构**

```bash
# 创建用户 profile wing
mempalace create-wing user-profile

# 创建当前项目 wing
mempalace create-wing projects/hermes-agent

# 创建知识库 wing
mempalace create-wing knowledge-base
```

**Step 4：编写 Hermes 集成脚本**

```python
# ~/.hermes/scripts/mempalace_wakeup.py
# 作用：在新会话开始时加载历史记忆

import subprocess
import json

PALACE_PATH = "~/palace"

def wake_up(query: str) -> str:
    """加载与 query 相关的记忆上下文"""
    result = subprocess.run(
        ["mempalace", "search", query, "--wing", "user-profile"],
        capture_output=True,
        text=True
    )
    return result.stdout

def save_session(session_id: str, content: str):
    """保存会话到 palace"""
    subprocess.run(
        ["mempalace", "mine", "--mode", "convos",
         "--session", session_id],
        input=content,
        text=True
    )

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    print(wake_up(query))
```

**Step 5：配置 Hermes cron 定时同步**

```yaml
# ~/.hermes/config.yaml
cron:
  enabled: true
  jobs:
    - name: mempalace-sync
      schedule: "0 */4 * * *"  # 每 4 小时
      script: ~/.hermes/scripts/mempalace_wakeup.py
      deliver: local
```

### 8.3 与现有 Context Engineering 技能联动

MemPalace 可与 Hermes Agent 已有的 Context Engineering skill 系统深度结合：

| Context Engineering 组件 | MemPalace 角色 |
|------------------------|----------------|
| **Protocol Shell** (davidkimai) | MemPalace 作为 intent/input 持久化存储 |
| **PRP 文档** (coleam00) | 生成的 PRP 存入对应 Wing/Room |
| **Gotchas 知识库** | `.gotchas/` 中的 YAML 条目可映射为 MemPalace Drawer |
| **Bayesian Context Inference** | MemPalace search 提供真实记忆检索作为 prior |

---

## 9. 验证安装成功

### 9.1 CLI 验证

```bash
mempalace --version
# → mempalace 3.3.2

mempalace --help
# → 显示完整命令列表

# 检查 palace 状态
mempalace status
# → Palace: ~/palace
# → Backend: chroma
# → Wings: 0
```

### 9.2 导入验证

```bash
python3 -c "
import mempalace
from mempalace.backends.base import BaseBackend
from mempalace.searcher import Searcher
print('MemPalace version:', mempalace.__version__)
print('Backend interface OK')
print('Searcher OK')
"
```

### 9.3 MCP 工具验证

```bash
# 启动 MCP server 并测试
mempalace mcp --stdio &
sleep 2

# 测试搜索（如果 palace 已有数据）
mempalace search "test query"
```

### 9.4 端到端验证流程

```bash
# 1. 创建测试 wing
mempalace create-wing test-wing

# 2. 添加测试内容
echo "This is a test drawer with sample content about Python programming." | \
  mempalace add-drawer test-wing "test room" --content -

# 3. 搜索验证
mempalace search "Python programming"

# 4. 验证结果包含预期内容
# Expected: "This is a test drawer..."

# 5. 清理测试数据
mempalace delete-wing test-wing --force
```

---

## 10. 卸载与数据迁移

### 10.1 卸载

```bash
# 方式 A：uv tool uninstall
uv tool uninstall mempalace

# 方式 B：pip uninstall
pip uninstall mempalace

# 清理 hook 脚本
rm -rf ~/.mempalace/hooks

# 清理状态文件
rm -rf ~/.mempalace/hook_state

# 重要：保留 palace 数据（默认在 ~/palace）
ls ~/palace
```

### 10.2 数据迁移

```bash
# 导出整个 palace
mempalace export ~/palace-export.tar.gz

# 导入到新机器
mempalace import ~/palace-export.tar.gz --to ~/new-palace

# 仅迁移特定 wing
mempalace export --wing user-profile --to ~/user-profile-export.json
```

### 10.3 升级

```bash
# uv
uv tool upgrade mempalace

# pipx
pipx upgrade mempalace

# pip
pip install --upgrade mempalace

# 开发模式
cd mempalace && git pull && uv sync
```

---

## 附录 A：故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `mempalace: command not found` | PATH 未包含 uv/pipx bin | `export PATH="$HOME/.local/bin:$PATH"` 或重新登录 |
| Hook 不触发（macOS GUI） | `MEMPAL_PYTHON` 未设置 | 在 hook 脚本设置 `MEMPAL_PYTHON="/usr/bin/python3"` |
| `chromadb` 启动失败 | 端口被占用 | `mempalace init --backend chroma --port 8097` |
| search 返回空 | 未执行 `mempalace mine` | `mempalace mine ~/projects --mode files` |
| MCP 连接失败 | 端口不匹配 | 检查 config.yaml 的 `mcp.port` 与客户端配置一致 |
| 导入报错 | Python 版本低于 3.9 | `python3 --version` 确认版本 |

## 附录 B：性能基准

| 操作 | 目标 | 实测 |
|------|------|------|
| Hook 触发延迟 | < 500ms | ~200ms（空 palace）|
| 启动注入延迟 | < 100ms | ~50ms |
| 搜索延迟（1000 drawers）| < 2s | ~800ms |
| Embedding 模型加载 | ~300MB | MiniLM-L6-v2: 90MB |

## 附录 C：相关资源

- **GitHub**: https://github.com/MemPalace/mempalace
- **文档**: https://mempalaceofficial.com
- **Discord**: https://discord.gg/ycTQQCu6kn
- **PyPI**: https://pypi.org/project/mempalace/
- **最新版本**: v3.3.2

---

*本指南基于 mempalace v3.3.2，GitHub API 数据截至 2026-04-21。*

# DeerFlow MCP Integration

## 概述

DeerFlow 是一个由 ByteDance 开源的多 Agent 研究框架，支持深度研究、web 搜索、工具调用和结构化报告生成。通过 MCP（Model Context Protocol）接入 Hermes Agent，使 Hermes 能够将复杂研究任务委托给 DeerFlow 处理。

**关键特性：**
- 自动 web 搜索 + 多步骤推理
- Thinking/CoT 推理模式
- 内置 21 个 Skills（工具集）
- 支持 MiniMax M2.7 等 OpenAI 兼容模型

## 架构

```
Hermes Agent
    └── MCP Client (stdio)
          └── deerflow_mcp.py          ← 桥接层
                └── DeerFlowClient
                      └── MiniMax M2.7 (api.minimaxi.com/v1)
                            └── DeerFlow Agent
                                  ├── web_search   (DuckDuckGo)
                                  ├── web_fetch    (Jina AI)
                                  ├── bash
                                  ├── file:read
                                  └── file:write
```

## 组件路径

| 组件 | 路径 |
|------|------|
| DeerFlow 源码 | `~/.hermes/deer-flow-repo/` |
| MCP 桥接层 | `~/.hermes/deerflow-mcp/deerflow_mcp.py` |
| DeerFlow venv | `~/.hermes/deer-flow-repo/backend/.venv/` |
| 模型配置 | `~/.hermes/deer-flow-repo/config.yaml` |

## 配置

### 1. 安装 DeerFlow

```bash
cd ~/.hermes/deer-flow-repo
uv venv backend/.venv --python 3.12
uv pip install -e ./backend
```

### 2. 配置模型（MiniMax M2.7 CN 区）

在 `~/.hermes/deer-flow-repo/config.yaml` 中添加：

```yaml
models:
  - name: minimax-m2.7
    display_name: MiniMax M2.7
    use: langchain_openai:ChatOpenAI
    model: MiniMax-M2.7
    api_key: $MINIMAX_API_KEY        # 从环境变量读取，不硬编码
    base_url: https://api.minimaxi.com/v1
    request_timeout: 120.0
    max_retries: 2
    temperature: 1.0
    supports_thinking: true
    supports_vision: true
```

### 3. 注册到 Hermes

在 `~/.hermes/config.yaml` 的 `mcp_servers:` 下添加：

```yaml
mcp_servers:
  deerflow:
    command: /Users/can/.hermes/deer-flow-repo/backend/.venv/bin/python
    args:
      - /Users/can/.hermes/deerflow-mcp/deerflow_mcp.py
    env:
      DEERFLOW_CONFIG_PATH: /Users/can/.hermes/deer-flow-repo/config.yaml
    enabled: true
```

重启 Hermes 使配置生效：
```bash
# 找到 Hermes 进程并重启
ps aux | grep hermes_cli | grep -v grep
kill <PID>
hermes gateway &
```

## 可用工具

| 工具 | 说明 |
|------|------|
| `deerflow_chat` | 发送研究任务，支持 thinking 推理，返回完整报告 |
| `deerflow_stream` | 流式输出，实时显示 agent 思考过程 |
| `deerflow_list_models` | 列出 config.yaml 中已配置的模型 |
| `deerflow_list_skills` | 列出 DeerFlow 内置的 21 个 skills |
| `deerflow_health` | 健康检查：模型数量、skills 数量、配置状态 |

## 使用示例

### 研究任务
```
用户 → Hermes → deerflow_chat(
  message="Research the latest developments in AI agents in 2025. Give me a 3-bullet summary."
)
→ DeerFlow 自动调用 web_search 获取最新资料
→ 综合回答（带 citations）
```

### 验证连接
```bash
hermes mcp test deerflow
# 预期：Connected, 5 tools discovered

hermes mcp list
# 预期：deerflow | stdio | all | ✓ enabled
```

## 安全说明

- **API Key 不写入文件**：通过 `DEERFLOW_CONFIG_PATH` 环境变量指向 config.yaml，config.yaml 中使用 `$MINIMAX_API_KEY` 环境变量占位符
- **DeerFlow venv 独立**：与 Hermes venv 完全隔离，独立升级
- **MCP stdio 传输**：进程随需启动，不监听网络端口

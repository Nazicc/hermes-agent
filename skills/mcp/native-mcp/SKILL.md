---
name: native-mcp
description: "Use when registering a new MCP server with hermes, adding or configuring MCP servers via CLI or config, debugging MCP tool discovery, connecting a custom FastMCP server, setting up MCP auto-start, resolving MCP connection failures, understanding hermes-agent MCP architecture, or connecting stdio-mode MCP servers. NOT for: browsing GitHub issues or comments, code review workflows, CI/CD automation, LLM API configuration, non-MCP tool integrations, or general network setup."
category: general
version: 1.0.0
...
author: Hermes Agent
...
---

# Native MCP — Built-in MCP Client

Built-in MCP (Model Context Protocol) client that connects to external MCP servers, discovers their tools, and registers them as native Hermes Agent tools. Supports stdio and HTTP transports with automatic reconnection, security filtering, and zero-config tool injection.

## Architecture


hermes-agent (MCP orchestrator)
  ├── MCP server 1 (stdio) → hermes spawns the subprocess
  ├── MCP server 2 (HTTP) → hermes connects as client
  └── MCP server N (stdio)


Hermes Agent uses the MCP Python SDK to manage external MCP servers. Servers communicate via **stdio** (subprocess stdin/stdout) or **HTTP** (SSE/streamable-http). The gateway process (`ai.hermes.gateway`) spawns MCP server subprocesses and proxies their tools to the LLM.

## Registering an MCP Server

### Via CLI (recommended)

bash
hermes mcp add <name> --command <cmd> --args <args...> --env <KEY=VALUE>
hermes mcp list          # Show all registered servers
hermes mcp test <name>   # Test a server connection
hermes mcp remove <name>  # Remove a server


**Examples:**

bash
# sirchmunk MCP server
hermes mcp add sirchmunk \
  --command sirchmunk \
  --args mcp serve \
  --env SIRCHMUNK_WORK_PATH=/Users/can/.hermes/sirchmunk-data

# custom FastMCP script
hermes mcp add myserver \
  --command /path/to/venv/bin/python \
  --args /path/to/mcp_server.py


### Via config.yaml

MCP servers are stored in `~/.hermes/config.yaml`:

yaml
mcp:
  <server_name>:
    command: <executable_path>
    args:
      - <arg1>
      - <arg2>
    env:
      <ENV_VAR>: <value>
    enabled: true


**Example:**

yaml
mcp:
  simplemem:
    command: /Users/can/.venv/bin/python
    args:
      - /Users/can/.hermes/scripts/simplemem_mcp.py
    enabled: true


## FastMCP Server Development

### FastMCP `__init__()` Gotchas (Critical)

**FastMCP does NOT accept these kwargs:**
- ❌ `description` — does not exist in installed version
- ❌ `dependencies` — does not exist in installed version

**FastMCP DOES accept:**
- ✅ `name: str`
- ✅ `instructions: str` (this is the description/instructions field)
- ✅ `website_url: str | None`
- ✅ `icons: list[Icon] | None`
- ✅ `retry_interval: int | None`
- ✅ `tool` kwarg accepts a list

**Always verify with:**
bash
~/.hermes/hermes-agent/venv/bin/python -c "from mcp.server.fastmcp import FastMCP; import inspect; print(inspect.signature(FastMCP.__init__))"


### FastMCP Example

python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="my-tool",
    instructions="What this tool does"
)

@mcp.tool()
def my_tool(arg1: str, arg2: int) -> str:
    """Tool description for the LLM."""
    return f"Result: {arg1} {arg2}"

if __name__ == "__main__":
    mcp.run()


## Stdio MCP Gotchas (Critical)

**`asyncio.TaskGroup` cannot be pickled across process boundaries.** If your MCP server uses `asyncio.TaskGroup` for concurrent operations and hermes-agent fails with `TypeError: cannot pickle 'locked' object`, switch to `subprocess.Popen` with explicit stdin/stdout communication instead of asyncio internals.

**Stdio MCP subprocess communication works across Python versions.** Even if hermes-agent runs Python 3.11 and the MCP server runs Python 3.12, stdio JSON-RPC communication works fine — the limitation is only with asyncio primitives that rely on pickling.

## Environment Variable Passing

**Env vars are NOT inherited by default.** When launching MCP servers via subprocess, hermes-agent uses `_build_safe_env()` which only passes a whitelist of `SAFE_ENV_KEYS`. To pass custom env vars:

1. Set them in the `env:` block in `config.yaml`
2. Or use `os.environ.setdefault()` in the MCP server script itself to read from the parent environment

## MCP Server Code Location

**MCP server code should live inside the hermes-agent git repo** (e.g., `hermes-agent/mcp-servers/<name>/`) NOT in `~/.hermes/` which is not git-tracked. This ensures version history and recovery capability.

## Auto-Start with launchd

The hermes gateway (`ai.hermes.gateway.plist`) auto-starts at login with `RunAtLoad=true` and `KeepAlive=true`. MCP servers registered in `config.yaml` auto-start with the gateway — no separate launchd entry needed for stdio servers.

For HTTP MCP servers that need their own persistent process:

bash
# Create plist at ~/Library/LaunchAgents/com.hermes.<name>.plist
launchctl load ~/Library/LaunchAgents/com.hermes.<name>.plist


## Troubleshooting

| Problem | Solution |
|---------|----------|
| `FastMCP.__init__() got an unexpected keyword argument 'description'` | Use `instructions` instead of `description`, remove `dependencies` |
| `cannot pickle 'locked' object` | Replace `asyncio.TaskGroup` with `subprocess.Popen` for stdio communication |
| MCP server not starting | Check `hermes mcp list` — server should show `✓ enabled` |
| Tools not discovered | Run `hermes mcp test <name>` to verify connection |
| Env vars not passed | Set them explicitly in `config.yaml` `env:` block or use `os.environ.setdefault()` |
| Wrong Python venv | Ensure the `command` uses the correct venv's Python |
| ModuleNotFoundError | The MCP server's venv must have all required packages |
| Port conflicts | HTTP transport servers must use unique ports |

**Debugging steps:**
1. Check registered servers: `hermes mcp list`
2. Test connection: `hermes mcp test <name>`
3. Inspect config: `grep -A10 'mcp:' ~/.hermes/config.yaml`
4. Server logs: Check the MCP server's own stdout/stderr (stdio mode)
5. Gateway logs: `tail -f ~/.hermes/logs/gateway.log`

## Related Skills

- `mcp-debugging` — Systematic debugging when MCP tools fail
- `simplemem-integration` — Example of wrapping a Python library as an MCP server

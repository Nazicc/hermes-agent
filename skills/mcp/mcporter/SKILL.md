---
name: mcporter
description: "Use the mcporter CLI (hermes mcp subcommands) to list, configure, and manage MCP server connections in hermes-agent. Covers hermes mcp add/list/test/serve/config for both stdio and HTTP transports, interactive prompts, per-server tool enablement, and standalone mcporter CLI usage."
category: general
---

## Quick Reference

bash
hermes mcp list                        # List all configured MCP servers
hermes mcp add <name>                   # Add a new MCP server (interactive)
hermes mcp test <name>                  # Test connectivity to a server
hermes mcp serve                        # Run hermes-agent as an MCP server
hermes mcp config <name>                # Show current server configuration
hermes mcp configure <name>             # Interactively enable/disable specific tools
hermes mcp remove <name>                # Remove a configured server


## Discovery & Status

bash
# List all configured MCP servers (shows name, transport, tools, status)
hermes mcp list

# Get help on a specific subcommand
hermes mcp --help
hermes mcp add --help


Example output:


MCP Servers:

  Name             Transport                      Tools        Status    
  ──────────────── ────────────────────────────── ──────────── ──────────
  sirchmunk        sirchmunk mcp serve            all          ✓ enabled


Status values: `enabled` (✓), `disabled`, or error state.

## Adding an MCP Server

### Stdio Transport

bash
hermes mcp add <name> --command <cmd> --args <args...> --env KEY=VALUE [--auth {oauth|header}]


**stdio mode**: hermes spawns the server process and communicates over stdin/stdout. The server process must be available in PATH.

**Example — sirchmunk MCP server:**
bash
hermes mcp add sirchmunk \
  --command sirchmunk \
  --args mcp serve \
  --env SIRCHMUNK_WORK_PATH=/Users/can/.hermes/sirchmunk-data


**Example — DeepCode MCP:**
bash
hermes mcp add deepcode \
  --command /Users/can/.openharness-venv/bin/python \
  --args /Users/can/DeepCode/deepcode_mcp.py \
  --env DEEPCODE_PORT=8000


The `hermes mcp add` command will:
1. Start the MCP server process to inspect its capabilities.
2. Prompt: `Enable all N tools? [Y/n/select]` — press Y (or pipe `echo "Y" |` for non-interactive).
3. Save the server config to `~/.hermes/config.yaml` under `mcpServers`.

**Non-interactive add (scripted):**
bash
echo "" | hermes mcp add sirchmunk --command sirchmunk --args mcp serve
# Empty stdin → defaults to Y (enable all)


### HTTP/SSE Transport

bash
hermes mcp add <name> --url <http-or-https-endpoint> [--auth header]


**Example — remote HTTP MCP server:**
bash
hermes mcp add remote-mcp \
  --url https://mcp.example.com:8080/mcp \
  --auth header \
  --env API_KEY=sk-...


### Auth Options

bash
hermes mcp add <name> --command <cmd> --auth oauth   # OAuth 2.0
hermes mcp add <name> --command <cmd> --auth header  # API key header


### Alternative: Manual Config Edit

If `hermes mcp add` is not available (older hermes version), edit `~/.hermes/config.yaml` directly:

yaml
mcpServers:
  <server-name>:
    command: <binary>
    args:
      - mcp
      - serve
    env:
      KEY: value


Then restart hermes. Run `hermes mcp list` to verify.

## Testing, Managing, and Removing Servers

bash
hermes mcp test <name>       # Test MCP server connection and discover tools
hermes mcp configure <name>   # Interactively enable/disable specific tools
hermes mcp config <name>     # Show current server configuration
hermes mcp remove <name>     # Remove a server


## Running hermes-agent as an MCP Server

Expose hermes-agent conversations as an MCP server (for use by Claude Desktop, Cursor, etc.):

bash
hermes mcp serve [--url <listen-url>]


## Configuration File

Servers are stored in `~/.hermes/config.yaml` under `mcpServers`:

yaml
mcpServers:
  <server-name>:
    command: <executable>
    args:
      - <arg1>
      - <arg2>
    env:
      KEY: VALUE
    tools: all  # or list specific tool names


## Stdio vs HTTP Transport

- **stdio mode** (default for `hermes mcp add`): hermes spawns the process as a child. The process does NOT run as a standalone HTTP server — no need for a launchd service or background daemon. Best for local servers that are always available.
- **HTTP mode** (`--url`): hermes connects to an already-running HTTP server. Best for remote servers or servers that run independently.

For sirchmunk specifically, use stdio mode with `sirchmunk mcp serve`. Do NOT confuse this with running `sirchmunk serve` (the API/HTTP server) or port 9283.

## Standalone mcporter CLI

The `mcporter` CLI is a standalone tool for ad-hoc MCP interactions (install via `pip install mcporter`).

### List servers

bash
mcporter servers list


### List tools on a server

bash
mcporter tools list --server <server_name>


### Call a tool

bash
mcporter tools call --server <server_name> --tool <tool_name> [--json-args '{"key": "value"}']


- Use `--json-args '{}'` for tools that take no arguments.
- For tools with positional args, pass them as a JSON array: `--json-args '[arg1, arg2]'`.
- mcporter auto-detects stdio vs HTTP based on the server config (`command`+`args` vs `url`).

### mcporter Config File

mcporter reads from `~/.config/mcporter/config.json` (or `$MCPORTER_CONFIG`):


{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      "env": {}
    }
  }
}


For HTTP servers:


{
  "mcpServers": {
    "http-example": {
      "url": "http://localhost:8080/mcp"
    }
  }
}


### HTTP Endpoints (Server Mode)

mcporter can serve tools over HTTP:

bash
mcporter serve --port 8080 --server <server_name>


This starts an HTTP server with SSE streaming at `/mcp`. Clients connect via:

bash
mcporter tools call --url http://localhost:8080/mcp --tool <tool_name> --json-args '{}'


### Auth Headers

Pass headers to MCP HTTP endpoints:

bash
mcporter tools call --url https://api.example.com/mcp \
  --header "Authorization: Bearer $TOKEN" \
  --tool <tool_name>


### CLI Reference

bash
mcporter --help
mcporter servers --help
mcporter tools --help
mcporter config --help
mcporter serve --help


## Integration Examples

### sirchmunk MCP Integration

bash
hermes mcp add sirchmunk \
  --command sirchmunk \
  --args mcp serve \
  --env SIRCHMUNK_WORK_PATH=/Users/can/.hermes/sirchmunk-data


sirchmunk exposes 1 tool: `sirchmunk_search`. Accept all tools at the prompt.

### deepcode MCP Integration

bash
hermes mcp add deepcode \
  --command /Users/can/.openharness-venv/bin/python \
  --args /Users/can/DeepCode/deepcode_mcp.py \
  --env DEEPCODE_PORT=8000


DeepCode exposes 9 tools including planning, requirements, and code generation.

## Quick Workflow

1. **Check existing**: `hermes mcp list` first — avoid duplicate registrations.
2. **Choose transport**: stdio (local CLI servers) or HTTP (remote servers).
3. **Add server**: `hermes mcp add <name>` with appropriate `--command`/`--url`.
4. **Test**: `hermes mcp test <name>` — verifies connectivity and discovers tools.
5. **Enable tools**: Accept all (Y) or select specific tools during add, or use `hermes mcp configure` later.
6. **Verify**: Run `hermes mcp list` — server shows `✓ enabled`.

## Edge Cases

- **Stuck process on port**: If an MCP server process is already running on a port, kill it with `pkill -f <process-name>` before adding via hermes.
- **Stdio server hanging**: If `hermes mcp test <name>` hangs, the server process is likely waiting on stdin. Press Ctrl+C and check the `--args` and `--env`.
- **Tool discovery fails**: Some servers require API keys in env vars. Set via `--env KEY=value`.
- **No tools found**: Some MCP servers require authentication env vars. Check the server's documentation and ensure all required `SIRCHMUNK_*` or custom env vars are set via `--env`.
- **Port already in use**: If a server command fails with "address already in use", find and kill the process on that port.
- **Multiple servers same port**: Each MCP server needs a unique port if using HTTP transport. Use `--env PORT=<unique-port>`.
- **Wrong transport type**: Using `--url` for a local stdio server (or vice versa) will fail. Match the transport to the server type.
- **Duplicate add**: `hermes mcp list` before adding. If already exists, remove first: `hermes mcp remove <name>`.

## Common Mistakes

### Wrong: Forgetting to set required env vars

bash
hermes mcp add sirchmunk --command sirchmunk --args mcp serve
# WRONG if the server requires SIRCHMUNK_WORK_PATH — will fail silently


**Always pass required env vars with `--env`.**

### Wrong: Using HTTP URL for a local stdio server

bash
hermes mcp add sirchmunk --url http://localhost:9283
# WRONG if sirchmunk uses stdio, not HTTP


**Match the transport to the server's capabilities.**

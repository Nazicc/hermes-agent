#!/bin/bash
# Keep stdin open so MCP stdio_server doesn't exit on EOF
exec python3 -c "
import sys, os, asyncio, logging
sys.path.insert(0, '/Users/can/.hermes/deer-flow-repo/backend/packages/harness')
os.environ.setdefault('DEERFLOW_CONFIG_PATH', '/Users/can/.hermes/deer-flow-repo/config.yaml')

# Block on a pipe read to keep stdin open until parent closes it
# This prevents stdio_server from seeing EOF and exiting immediately
import os, threading
r, w = os.pipe()
def keep_open():
    try:
        os.close(w)
        os.read(r, 1)  # blocks until parent closes write end
    except: pass
t = threading.Thread(target=keep_open, daemon=True)
t.start()

# Now import and run the real MCP server
from mcp.server import Server
from mcp.server.stdio import stdio_server
from deerflow_mcp import server as deerflow_server, APP_NAME

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(APP_NAME)

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await deerflow_server.run(read_stream, write_stream, deerflow_server.create_initialization_options())

asyncio.run(main())
" /Users/can/.hermes/hermes-agent/mcp-servers/deerflow-mcp/deerflow_mcp.py
chmod +x /Users/can/.hermes/hermes-agent/mcp-servers/deerflow-mcp/run-deerflow-mcp.sh
echo "Wrapper created"

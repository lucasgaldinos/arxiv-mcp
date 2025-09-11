#!/usr/bin/env python3
"""
Minimal MCP server test to isolate the tuple error
"""
import asyncio
import json
import sys
sys.path.append('src')

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import ListToolsResult, Tool

# Create a minimal server
test_app = Server("test-server")

@test_app.list_tools()
async def test_list_tools() -> ListToolsResult:
    """Test tools listing."""
    return ListToolsResult(
        tools=[
            Tool(
                name="test_tool",
                description="A simple test tool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Test query"}
                    },
                    "required": ["query"]
                }
            )
        ]
    )

async def test_via_stdio():
    """Test the server via stdio protocol"""
    import subprocess
    
    # Create a test script that runs our minimal server
    test_script = '''
import asyncio
import sys
sys.path.append('src')

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import ListToolsResult, Tool

app = Server("test-server")

@app.list_tools()
async def handle_list_tools():
    return ListToolsResult(
        tools=[
            Tool(
                name="test_tool",
                description="A simple test tool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Test query"}
                    },
                    "required": ["query"]
                }
            )
        ]
    )

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Write test script
    with open('/tmp/test_mcp_server.py', 'w') as f:
        f.write(test_script)
    
    # Test it
    proc = subprocess.Popen(
        ['python3', '/tmp/test_mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd='/home/lucas_galdino/repositories/mcp_servers/arxiv-mcp-improved'
    )
    
    try:
        # Initialize
        init_msg = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2025-06-18',
                'capabilities': {'tools': {}},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }
        
        proc.stdin.write(json.dumps(init_msg) + '\n')
        proc.stdin.flush()
        
        # Read init response
        init_response = proc.stdout.readline()
        print("Init response:", init_response.strip())
        
        # Send initialized notification
        initialized_msg = {
            'jsonrpc': '2.0',
            'method': 'notifications/initialized',
            'params': {}
        }
        proc.stdin.write(json.dumps(initialized_msg) + '\n')
        proc.stdin.flush()
        
        # Send tools/list
        list_msg = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/list',
            'params': {}
        }
        
        proc.stdin.write(json.dumps(list_msg) + '\n')
        proc.stdin.flush()
        
        # Read tools response
        tools_response = proc.stdout.readline()
        print("Tools response:", tools_response.strip())
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(test_via_stdio())

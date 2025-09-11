#!/usr/bin/env python3
"""
Debug script to test MCP server functionality
"""
import asyncio
import json
import sys
sys.path.append('src')

from arxiv_mcp.tools import handle_list_tools

async def main():
    try:
        print("Testing handle_list_tools directly...")
        result = await handle_list_tools()
        
        print(f"✓ Success! Found {len(result.tools)} tools")
        
        # Test serialization
        tools_data = []
        for i, tool in enumerate(result.tools):
            try:
                tool_dict = {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                tools_data.append(tool_dict)
                print(f"  {i+1}. {tool.name} - OK")
            except Exception as e:
                print(f"  {i+1}. Error with tool: {e}")
                print(f"      Tool type: {type(tool)}")
                print(f"      Tool value: {tool}")
                
        print(f"\n✓ All {len(tools_data)} tools serialized successfully")
        
        # Test JSON serialization
        json_result = json.dumps({"tools": tools_data}, indent=2)
        print("✓ JSON serialization successful")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

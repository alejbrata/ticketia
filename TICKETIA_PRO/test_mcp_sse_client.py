import asyncio
import json
import httpx
from mcp.client.sse import sse_client
from mcp import ClientSession

async def test_sse_server():
    print("🚀 Connecting to SSE MCP Server...")
    
    # URL for the SSE endpoint. FastMCP create_starlette_app() uses /sse by default
    url = "http://localhost:8000/sse"

    # sse_client handles the connection and message transport
    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()
            print("✅ Initialized session.")
            
            # List tools
            tools_response = await session.list_tools()
            print("\n🛠️  Available Tools:")
            for tool in tools_response.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Example call to the tool
            try:
                print("\n🔧 Calling get_financial_summary...")
                result = await session.call_tool("get_financial_summary", {"user_phone": "+34600000000"})
                print("📊 Result:")
                if result.content:
                    print(result.content[0].text)
                else:
                    print("No text result.")
            except Exception as e:
                print(f"Failed to call tool: {e}")

if __name__ == "__main__":
    asyncio.run(test_sse_server())

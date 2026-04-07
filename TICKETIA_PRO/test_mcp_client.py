import asyncio
import os
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables (for OPENAI_API_KEY)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

async def main():
    print("🚀 Starting MCP Proof of Concept Client...")
    
    # Initialize AsyncOpenAI client
    client = AsyncOpenAI() # Uses OPENAI_API_KEY from environment
    
    # 1. Define Server Parameters
    # We run the FastMCP server we just created using the python executable
    script_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
    server_params = StdioServerParameters(
        command="python",
        args=[script_path],
        env=os.environ.copy() # Pass env vars so Flask app can connect to DB
    )
    
    # 2. Connect to the MCP Server
    print("🔌 Connecting to local MCP server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            print("✅ Session initialized.")
            
            # 3. Discover Tools
            tools_response = await session.list_tools()
            available_tools = []
            print(f"🛠️  Discovered {len(tools_response.tools)} tools:")
            
            for tool in tools_response.tools:
                print(f"  - {tool.name}: {tool.description}")
                # Convert MCP Tool to OpenAI Tool Format
                available_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

            # 4. Simulate the Agent's Context
            print("\n🤖 Sending request to El Gestor (GPT-4o) with MCP tools connected...")
            phone_number_to_test = "+34600000000" # Replace with a real phone from DB for testing
            
            messages = [
                {
                    "role": "system", 
                    "content": "Eres 'El Gestor'. Ayudas a los autónomos. Tienes acceso a herramientas para buscar en internet."
                },
                {
                    "role": "user", 
                    "content": "Hola, ¿puedes buscarme en el BOE si hay alguna noticia reciente sobre ayudas para digitalización de empresas?"
                }
            ]
            
            # 5. Call OpenAI with the available tools
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=available_tools
            )
            
            response_message = response.choices[0].message
            print(f"🤔 Gestor's initial response (Tool Calls: {bool(response_message.tool_calls)})")
            
            messages.append(response_message)
            
            # 6. Execute True "Agentic" Loop if a tool call was requested
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    print(f"🔧 Calling Tool: {tool_call.function.name}")
                    args = json.loads(tool_call.function.arguments)
                    
                    # Execute tool via MCP Server
                    result = await session.call_tool(tool_call.function.name, arguments=args)
                    
                    # MCP returns a list of contents (text/image)
                    tool_result_content = result.content[0].text if result.content else "No result."
                    print(f"📊 Tool Result received from Server: {len(tool_result_content)} characters")
                    
                    # Append result back to the LLM conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": tool_result_content
                    })
                    
                # 7. Final Reasoning from the Agent with data
                print("\n🧠 Gestor is analyzing the data...")
                final_response = await client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                )
                print(f"\n✅ Result:\n{final_response.choices[0].message.content}")
            else:
                print(f"\n✅ Result:\n{response_message.content}")
                
            print("\n🎉 PoC Complete!")

if __name__ == "__main__":
    asyncio.run(main())

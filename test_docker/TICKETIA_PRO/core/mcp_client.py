import asyncio
import os
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

class TicketiaMCPClient:
    """
    Client that connects to the local FastMCP server (mcp_server.py)
    to provide tools (Calendar, Web Search, EMail) to the OpenAI agents.
    """
    def __init__(self):
        self._openai = AsyncOpenAI()
        self.server_script = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "mcp_server.py"
        )
        
        pass # We will use async with directly in execute_agent_loop

    async def execute_agent_loop(self, system_prompt: str, user_message: str):
        """
        Executes a single interaction loop using MCP tools.
        Returns the final text string to send back to the user.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            server_params = StdioServerParameters(
                command="python",
                args=[self.server_script],
                env=os.environ.copy()
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Get tools
                    tools_response = await session.list_tools()
                    openai_tools = []
                    for tool in tools_response.tools:
                        openai_tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.inputSchema
                            }
                        })
                    
                    # Initial Call
                    response = await self._openai.chat.completions.create(
                        model="gpt-4o",
                        messages=messages,
                        tools=openai_tools
                    )
                    
                    response_msg = response.choices[0].message
                    messages.append(response_msg)
                    
                    # Check for tool calls
                    if response_msg.tool_calls:
                        for tool_call in response_msg.tool_calls:
                            print(f"🔧 Agent requested tool: {tool_call.function.name}")
                            args = json.loads(tool_call.function.arguments)
                            
                            try:
                                # Execute the tool on the MCP server
                                result = await session.call_tool(tool_call.function.name, arguments=args)
                                tool_result_content = result.content[0].text if result.content else "Exito sin salida."
                            except Exception as e:
                                tool_result_content = f"Error executing tool: {e}"
                                
                            # Append result
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": tool_result_content
                            })
                        
                        # Final evaluation call with tool results
                        final_response = await self._openai.chat.completions.create(
                            model="gpt-4o",
                            messages=messages
                        )
                        final_text = final_response.choices[0].message.content
                    else:
                        final_text = response_msg.content

            return final_text
            
        except Exception as e:
            print(f"❌ Error in MCP Execute Loop: {e}")
            return f"Hubo un error del sistema contactando a las herramientas: {e}"

# Singleton helper if needed
_mcp_client = None
def get_mcp_client():
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = TicketiaMCPClient()
    return _mcp_client

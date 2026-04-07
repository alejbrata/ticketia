import asyncio
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from modules.council.orchestrator import CouncilManager

async def test_council():
    print("🚀 Starting Async Council Manager Test with MCP...")
    
    council = CouncilManager()
    
    # Simulating a user context
    user_context = "Usuario de prueba: +34123456789. Negocio: Reformas SL."
    topic = "Quiero saber si hay ayudas vigentes en el BOE para reformistas en Madrid."
    
    print(f"🧐 Topic: {topic}\n")
    
    # We iterate over the async generator
    try:
        async for message in council.run_session(topic, user_context, use_mcp=True):
            if message["type"] == "message":
                print(f"[{message['emoji']} {message['name']}] {message['text']}\n")
            elif message["type"] == "plan":
                print(f"📋 **PLAN FINAL**:\n{message['text']}\n")
    except Exception as e:
        print(f"❌ Error during Council Session: {e}")

if __name__ == "__main__":
    asyncio.run(test_council())

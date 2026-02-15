import os
import json
import sys
from openai import OpenAI

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.clients import get_openai_client

# Mocking App Context for Agents
from app import app
from modules.agents.manager import run_agent
from core.db_models import BusinessProfile

def evaluate_agents():
    print("🧪 Starting Agent Evaluation (LLM-as-a-Judge)...")
    
    # Load Dataset
    try:
        with open('mlops/datasets/gold_standard.json', 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print("❌ Dataset not found. Run from project root.")
        return

    client = get_openai_client()
    results = []

    # Mock User Context
    with app.app_context():
        # Ensure a dummy user exists/is loaded for context
        user = BusinessProfile.query.first()
        if not user:
            print("⚠️ No user in DB. Evaluation might be limited.")
            # In a real pipeline, we would seed a test user here.

        for case in dataset:
            print(f"\n🔹 Testing Input: '{case['input']}'")
            
            # 1. Run Agent
            # Note: We run passing a dummy phone if needed, or mocking session
            # For simplicity, we assume the agent manager handles it or we mock it.
            # Manager expects: user_message, phone_number, business_profile
            try:
                agent_response = run_agent(
                    user_message=case['input'], 
                    phone_number=user.user_phone if user else "000000000",
                    business_profile=user
                )
            except Exception as e:
                agent_response = f"ERROR: {str(e)}"

            print(f"   🤖 Agent Output: {agent_response[:100]}...")

            # 2. Evaluate with Judge (GPT-4o)
            judge_prompt = f"""
            You are an impartial judge evaluation an AI Agent.
            
            INPUT: {case['input']}
            EXPECTED INTENT: {case['expected_intent']}
            CRITERIA: {case['criteria']}
            
            ACTUAL AGENT RESPONSE: 
            "{agent_response}"
            
            TASK:
            Does the agent response meet the criteria? 
            Responde JSON: {{ "score": (0-1), "reason": "concise explanation" }}
            """
            
            try:
                eval_resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": judge_prompt}],
                    response_format={"type": "json_object"}
                )
                eval_result = json.loads(eval_resp.choices[0].message.content)
            except Exception as e:
                eval_result = {"score": 0, "reason": f"Judge Error: {e}"}

            print(f"   ⚖️ Score: {eval_result['score']} | Reason: {eval_result['reason']}")
            
            results.append({
                "input": case['input'],
                "score": eval_result['score'],
                "reason": eval_result['reason']
            })

    # Summary
    total_score = sum(r['score'] for r in results)
    avg_score = total_score / len(results) if results else 0
    print(f"\n📊 FINAL REPORT: Avg Score = {avg_score:.2f}")
    
    if avg_score < 0.7:
        print("❌ FAILED: Overall quality below threshold.")
        sys.exit(1)
    else:
        print("✅ PASSED: Quality meets standards.")
        sys.exit(0)

if __name__ == "__main__":
    evaluate_agents()

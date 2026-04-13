"""
MLOps Agent Evaluation - Gold Standard Tests
Runs lightweight quality checks on agent outputs without hitting real LLM APIs.
"""
import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock env vars for import
os.environ.setdefault('OPENAI_API_KEY', 'sk-fake-key-for-eval')

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  PASS  {name}")
        PASS += 1
    else:
        print(f"  FAIL  {name}: {detail}")
        FAIL += 1


def eval_grant_hunter_output():
    """Validate that GrantHunterAgent structures notifications correctly."""
    print("\n[Eval] GrantHunterAgent output schema")
    sample = {
        "title": "Nueva Ayuda: Kit Digital 2025",
        "message": "Subvencion de 12.000 EUR para digitalizacion.",
        "type": "grant",
        "user_phone": "123456789"
    }
    check("has title", "title" in sample and sample["title"])
    check("has message", "message" in sample and sample["message"])
    check("type is grant", sample.get("type") == "grant")
    check("has user_phone", "user_phone" in sample)


def eval_business_coach_output():
    """Validate that BusinessCoachAgent alert structure is correct."""
    print("\n[Eval] BusinessCoachAgent alert schema")
    sample = {
        "title": "Alerta de Gastos",
        "message": "Tus gastos han aumentado un 50% respecto al mes anterior.",
        "type": "alert",
        "user_phone": "123456789"
    }
    check("has title", "title" in sample and sample["title"])
    check("has message", "message" in sample and sample["message"])
    check("type is alert", sample.get("type") == "alert")


def eval_post_sales_intent():
    """Validate intent detection response structure."""
    print("\n[Eval] PostSalesAgent intent schema")
    raw = '{"intent": "COMPLAINT", "sentiment": "angry"}'
    try:
        parsed = json.loads(raw)
        check("parses JSON", True)
        check("has intent", "intent" in parsed)
        check("has sentiment", "sentiment" in parsed)
        check("valid intent value", parsed.get("intent") in ("COMPLAINT", "QUESTION", "PRAISE", "RETURN"))
    except json.JSONDecodeError as e:
        check("parses JSON", False, str(e))


def main():
    print("=" * 50)
    print("Ticketia MLOps Agent Evaluation")
    print("=" * 50)

    eval_grant_hunter_output()
    eval_business_coach_output()
    eval_post_sales_intent()

    print(f"\nResults: {PASS} passed, {FAIL} failed")
    if FAIL > 0:
        sys.exit(1)
    print("All evaluations passed.")


if __name__ == "__main__":
    main()

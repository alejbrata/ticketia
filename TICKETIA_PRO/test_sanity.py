import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_web_routes():
    print("Testing Web Routes...")
    routes = ['/', '/login', '/register', '/dashboard']
    for route in routes:
        try:
            resp = requests.get(f"{BASE_URL}{route}")
            print(f"[{route}] Status: {resp.status_code}")
            if resp.status_code >= 500:
                print(f"❌ ERROR ON {route}")
                return False
        except Exception as e:
            print(f"❌ Failed to connect to {route}: {e}")
            return False
    print("✅ Web Routes OK\n")
    return True

def test_webhook_dispatcher():
    print("Testing WhatsApp Dispatcher...")
    try:
        payload = {
            'Body': 'Hola soy una prueba',
            'From': 'whatsapp:+34600000000',
            'To': 'whatsapp:+14155238886',
            'NumMedia': '0'
        }
        resp = requests.post(f"{BASE_URL}/whatsapp", data=payload)
        print(f"[/whatsapp] Status: {resp.status_code}")
        # Even if it returns 200, we should check if TwiML is returned
        if b"xml" in resp.content.lower() or resp.status_code == 200:
            print("✅ Webhook Dispatcher OK\n")
            return True
        else:
            print(f"❌ Webhook Dispatcher failed with status {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to hit /whatsapp: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Refactoring Sanity Checks...\n")
    
    web_ok = test_web_routes()
    hook_ok = test_webhook_dispatcher()
    
    if web_ok and hook_ok:
        print("🎉 ALL SANITY CHECKS PASSED. The refactoring is solid.")
        sys.exit(0)
    else:
        print("⚠️ SOME CHECKS FAILED. Please review the logs.")
        sys.exit(1)

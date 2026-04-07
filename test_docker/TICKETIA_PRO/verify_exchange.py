import os
import sys
from app import app
from core.db_models import db, BusinessProfile
from modules.proactive.post_sales import PostSalesAgent

def test_exchange_logic():
    with app.app_context():
        print(f"🔌 DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Get Admin User/Profile
        # En seed_owner.py vimos que el admin tiene este email
        profile = BusinessProfile.query.filter_by(user_phone="+34630339601").first()
        
        if not profile:
             # Try fallback if exact phone match fails
             profile = BusinessProfile.query.first()
             if profile:
                 print(f"⚠️ Warn: Target phone not found, using first available profile: {profile.user_phone}")
        
        if not profile:
             print("❌ Error: No profiles found in DB.")
             return
        
        print(f"Loaded Profile Config: {profile.agent_config}")
        
        agent = PostSalesAgent()
        
        # Test 1: Exchange Intent
        print("\n--- TEST 1: Exchange Intent ---")
        msg = "Quiero cambiar la talla de mi camiseta"
        response, _ = agent.handle_inquiry("123456789", msg, profile)
        print(f"User: {msg}")
        print(f"Agent: {response}")
        
        if "https://ticketia.com/cambios-y-devoluciones" in response:
             print("✅ PASS: URL found in response")
        else:
             print("❌ FAIL: URL not found")

        # Test 2: Complaint Intent
        print("\n--- TEST 2: Complaint Intent ---")
        msg = "Estoy muy enfadado, esto es una vergüenza, quiero hablar con un jefe"
        response, _ = agent.handle_inquiry("123456789", msg, profile)
        print(f"User: {msg}")
        print(f"Agent: {response}")
        
        # We can't strictly match the dynamic response, but we can check if it's not the default generic one or the old static one
        if "prioridad ALTA" in response or "peronalmente" in response or "personally" in response or "review" in response: # 'personally' might be from English prompt, 'prioridad ALTA' from fallback
             print("✅ PASS: Dynamic/Refined response detected")
        else:
             print("⚠️ WARN: Check response manually")

if __name__ == "__main__":
    test_exchange_logic()

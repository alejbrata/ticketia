import os
from openai import OpenAI
from twilio.rest import Client
from runwayml import RunwayML
from core.config import Config

# --- Singleton Clients ---

# OpenAI
_openai_client = None

def get_openai_client():
    global _openai_client
    if _openai_client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ Warning: OPENAI_API_KEY not found.")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client

# Twilio
_twilio_client = None

def get_twilio_client():
    global _twilio_client
    if _twilio_client is None:
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        if not account_sid or not auth_token:
            print("⚠️ Warning: Twilio credentials not found.")
        try:
            _twilio_client = Client(account_sid, auth_token)
        except Exception as e:
            print(f"❌ Error initializing Twilio client: {e}")
    return _twilio_client

# RunwayML
_runway_client = None

def get_runway_client():
    global _runway_client
    if _runway_client is None:
        api_key = Config.RUNWAYML_API_SECRET
        if not api_key:
            print("⚠️ Warning: RUNWAYML_API_SECRET not found.")
        try:
            _runway_client = RunwayML(api_key=api_key)
        except Exception as e:
            print(f"❌ Error initializing Runway client: {e}")
    return _runway_client

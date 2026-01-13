import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'TICKETIA_PRO')))

from TICKETIA_PRO.app import app, db
from TICKETIA_PRO.core.db_models import BusinessProfile
import json

def check_db():
    with app.app_context():
        profile = BusinessProfile.query.first()
        if profile:
            print(f"Profile: {profile.business_name}")
            print(f"Static Knowledge Type: {type(profile.static_knowledge)}")
            print(f"Static Knowledge Content: {json.dumps(profile.static_knowledge, indent=2)}")
        else:
            print("No profile found")

if __name__ == "__main__":
    check_db()

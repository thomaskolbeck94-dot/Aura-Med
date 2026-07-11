import sys
import os

# Add src to python path so we can import auramed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from auramed.core.database_setup import SessionLocal, init_saas_db
from auramed.core.models_db import Client, APIKey
import secrets

def create_test_client(email="test@example.com"):
    # Ensure DB tables exist
    init_saas_db()
    
    db = SessionLocal()
    try:
        # Check if client already exists
        client = db.query(Client).filter(Client.email == email).first()
        if not client:
            client = Client(email=email)
            db.add(client)
            db.commit()
            db.refresh(client)
            print(f"Created new Client ID: {client.id}")
        else:
            print(f"Client {email} already exists with ID: {client.id}")
            
        # Generate new API key
        raw_key = f"aura_live_{secrets.token_urlsafe(24)}"
        api_key = APIKey(key=raw_key, client_id=client.id)
        db.add(api_key)
        db.commit()
        
        print(f"\n--- NEW API KEY GENERATED ---")
        print(f"Key: {raw_key}")
        print(f"Client: {email}")
        print(f"-----------------------------\n")
        
        return raw_key
    finally:
        db.close()

if __name__ == "__main__":
    create_test_client()

import sys
import os

# Add src to python path so we can import auramed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from fastapi.testclient import TestClient
from auramed.api import app

client = TestClient(app)

def test_stripe_flow():
    print("--- 1. Simuliere Stripe Webhook (Zahlung erfolgreich) ---")
    mock_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_a1b2c3d4e5",
                "customer": "cus_test_123",
                "subscription": "sub_test_456",
                "customer_details": {
                    "email": "kunde@arztpraxis.de"
                }
            }
        }
    }
    
    response = client.post("/api/v1/stripe/webhook", json=mock_payload)
    print(f"Webhook Response: {response.status_code}")
    
    print("\n--- 2. Simuliere Aufruf der 'Vielen Dank' Seite ---")
    response = client.get("/api/v1/stripe/retrieve_key?session_id=cs_test_a1b2c3d4e5")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Erfolg! Key abgeholt: {data['api_key']}")
        print(f"E-Mail: {data['email']}")
    else:
        print(f"Fehler: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_stripe_flow()

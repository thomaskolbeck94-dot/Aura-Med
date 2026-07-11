import stripe
import os
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import secrets
from auramed.core.database_setup import get_db
from auramed.core.models_db import Client, APIKey

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

router = APIRouter(prefix="/api/v1/stripe", tags=["stripe"])

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        if endpoint_secret and endpoint_secret != "whsec_dummy":
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        else:
            # For testing without signature validation
            import json
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        customer_email = session.get("customer_details", {}).get("email")
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        checkout_session_id = session.get("id")
        
        if customer_email:
            # Check if client exists
            client = db.query(Client).filter(Client.email == customer_email).first()
            if not client:
                client = Client(email=customer_email)
                db.add(client)
            
            client.stripe_customer_id = customer_id
            client.stripe_subscription_id = subscription_id
            client.checkout_session_id = checkout_session_id
            
            db.commit()
            db.refresh(client)
            
            # Generate new API key
            raw_key = f"aura_live_{secrets.token_urlsafe(24)}"
            api_key = APIKey(key=raw_key, client_id=client.id)
            db.add(api_key)
            db.commit()
            
            print(f"Stripe Webhook: Created Key {raw_key} for {customer_email}")
            
    elif event['type'] in ['customer.subscription.deleted', 'invoice.payment_failed']:
        # Block API key if subscription cancelled or payment failed
        data_object = event['data']['object']
        customer_id = data_object.get('customer')
        
        if customer_id:
            client = db.query(Client).filter(Client.stripe_customer_id == customer_id).first()
            if client:
                client.is_active = False
                for api_key in client.api_keys:
                    api_key.is_active = False
                db.commit()
                print(f"Stripe Webhook: Disabled access for Client {client.email}")

    return {"status": "success"}

@router.get("/retrieve_key")
def retrieve_key(session_id: str, db: Session = Depends(get_db)):
    """
    Abruf des generierten API-Keys anhand der Checkout Session ID.
    Wird von der "Vielen Dank"-Landingpage aufgerufen.
    """
    # Find client by session_id
    client = db.query(Client).filter(Client.checkout_session_id == session_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Get the latest API key
    api_key = db.query(APIKey).filter(APIKey.client_id == client.id).order_by(APIKey.created_at.desc()).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="Key not found")
        
    return {
        "success": True,
        "api_key": api_key.key, 
        "email": client.email
    }

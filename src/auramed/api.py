from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Security, status, Depends, Request
from fastapi.security import APIKeyHeader
from typing import Optional
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware

from auramed.models import ScanResponse
from auramed.core.database import is_valid_api_key, increment_api_key_usage
from auramed.core.scanner import process_scan
from auramed.core.homeassistant import push_scan_to_homeassistant
from auramed.routers import stripe as stripe_router

# Setup Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="AuraMed API",
    description="Intelligente Haltbarkeitsüberwachung von Medikamenten",
    version="0.1.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stripe_router.router)

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    require_key = os.getenv("REQUIRE_API_KEY", "false").lower() == "true"
    
    if not require_key:
        return True 
        
    is_valid_key = is_valid_api_key(api_key)
    
    if not is_valid_key:
        stripe_link = os.getenv("STRIPE_PAYMENT_LINK", "https://buy.stripe.com/your_link_here")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"API Key fehlt oder ungültig. Hole dir deinen Key unter: {stripe_link}"
        )
        
    if not increment_api_key_usage(api_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Tägliches Limit von 100 Scans für diesen API-Key erreicht. Bitte versuche es morgen wieder."
        )
        
    return api_key

@app.post("/api/v1/scan", response_model=ScanResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def scan_package(
    request: Request,
    background_tasks: BackgroundTasks,
    raw_barcode: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    """
    Endpunkt zum Verarbeiten eines Medikamenten-Scans.
    Akzeptiert entweder einen rohen Barcode-String oder ein Bild.
    Rate-Limited auf 30 Anfragen pro Minute pro IP.
    """
    image_bytes = None
    if image:
        image_bytes = await image.read()
        
    response = await process_scan(raw_barcode, image_bytes)
    
    if response.success and response.data:
        background_tasks.add_task(push_scan_to_homeassistant, response.data)
        
    return response

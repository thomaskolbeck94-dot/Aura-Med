from pydantic import BaseModel
from typing import Optional, Dict, Any

class ScanData(BaseModel):
    pzn: str
    medication_name: str
    expiry_date: str
    batch_lot: str
    serial_number: str
    refill_link: Optional[str] = None

class ScanResponse(BaseModel):
    success: bool
    source: str
    data: Optional[ScanData] = None
    error: Optional[str] = None
    
class ScanRequest(BaseModel):
    raw_barcode: Optional[str] = None
    # For file uploads, FastAPI uses UploadFile instead of Pydantic models directly,
    # but we can accept a JSON payload if they just send the barcode string.

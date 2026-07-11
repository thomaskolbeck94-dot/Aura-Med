from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Security, status, Depends
from fastapi.security import APIKeyHeader
from typing import Optional
import os
from auramed.models import ScanResponse, ScanData
from auramed.core.database import lookup_pzn, is_valid_api_key
from auramed.core.pzn_validator import is_valid_pzn
from auramed.core.date_math import parse_gs1_expiry_date
from auramed.core.decoder import decode_datamatrix_from_bytes
from auramed.core.ocr import run_ocr_extraction
from auramed.core.affiliate import generate_refill_link
from auramed.core.homeassistant import push_scan_to_homeassistant
from auramed.core.image_utils import convert_to_jpeg_bytes
import re
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="AuraMed API",
    description="Intelligente Haltbarkeitsüberwachung von Medikamenten",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted to https://getauramed.de
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# Türsteher-Logik für API-Keys (SaaS Monetarisierung)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    require_key = os.getenv("REQUIRE_API_KEY", "false").lower() == "true"
    
    if not require_key:
        return True # Für lokale Open-Source Nutzung
        
    is_valid_key = is_valid_api_key(api_key)
    
    if not is_valid_key:
        stripe_link = os.getenv("STRIPE_PAYMENT_LINK", "https://buy.stripe.com/your_link_here")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"API Key fehlt oder ungültig. Hole dir deinen Key unter: {stripe_link}"
        )
    return api_key

def dummy_gs1_parser(barcode: str):
    """
    Ein rudimentärer Parser für GS1 DataMatrix Strings für erste Tests.
    Erwartet ein Format wie (01)04150000000000(17)280500(10)CH123(21)SN987
    In Realität können die Klammern fehlen und unsichtbare Trennzeichen (FNC1) vorhanden sein.
    """
    # Extrahiere GTIN (AI 01)
    gtin_match = re.search(r'\(?01\)?(\d{14})', barcode)
    # Extrahiere EXP (AI 17)
    exp_match = re.search(r'\(?17\)?(\d{6})', barcode)
    # Extrahiere BATCH (AI 10)
    batch_match = re.search(r'\(?10\)?([A-Za-z0-9]+)', barcode)
    # Extrahiere SERIAL (AI 21)
    serial_match = re.search(r'\(?21\)?([A-Za-z0-9]+)', barcode)

    if not (gtin_match and exp_match and batch_match and serial_match):
        raise ValueError("Barcode enthält nicht alle erforderlichen GS1 AIs (01, 17, 10, 21)")

    # GTIN enthält in Deutschland die PZN ab der 5. Stelle (z.B. 04150 + 8-stellige PZN + Prüfziffer)
    # Für unseren simplen Test nehmen wir an, die letzten 8 Stellen vor der GTIN-Prüfziffer sind die PZN
    # Oder wir extrahieren sie rudimentär (Länge 14: Index 5 bis 13)
    gtin = gtin_match.group(1)
    pzn = gtin[5:13] # Dies ist eine vereinfachte Annahme für deutsche NTINs!
    
    exp_date = parse_gs1_expiry_date(exp_match.group(1))

    return {
        "pzn": pzn,
        "expiry_date": exp_date,
        "batch_lot": batch_match.group(1),
        "serial_number": serial_match.group(1)
    }


@app.post("/api/v1/scan", response_model=ScanResponse, dependencies=[Depends(verify_api_key)])
async def scan_package(
    background_tasks: BackgroundTasks,
    raw_barcode: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None)
):
    """
    Endpunkt zum Verarbeiten eines Medikamenten-Scans.
    Akzeptiert entweder einen rohen Barcode-String oder ein Bild.
    """
    source = "datamatrix"
    
    if image:
        image_bytes = await image.read()
        image_bytes = convert_to_jpeg_bytes(image_bytes)
        
        # 1. Try to decode GS1 DataMatrix
        raw_barcode = decode_datamatrix_from_bytes(image_bytes)
        
        if raw_barcode:
            source = "datamatrix_image"
        else:
            # 2. Fallback to OCR
            source = "ocr_fallback"
            ocr_data = run_ocr_extraction(image_bytes)
            
            pzn = ocr_data.get("pzn")
            
            if not pzn:
                return ScanResponse(
                    success=False,
                    source=source,
                    error="Kein DataMatrix Code gefunden und OCR konnte keine PZN extrahieren."
                )
                
            # Simulate parsed data for OCR path
            # OCR logic might return different date formats, so we just pass it through
            parsed_data = {
                "pzn": pzn,
                "expiry_date": ocr_data.get("expiry_date", "Unbekannt"),
                "batch_lot": "Unbekannt (OCR)",
                "serial_number": "Unbekannt (OCR)"
            }
            
            # Skip the raw_barcode logic and jump to db lookup
            raw_barcode = None
            
            # Wir rufen direkt die DB-Abfrage für OCR Ergebnisse auf
            if not is_valid_pzn(pzn):
                raise HTTPException(status_code=400, detail=f"Ungültige PZN aus OCR extrahiert: {pzn}")
                
            med_info = lookup_pzn(pzn)
            med_name = med_info["name"] if med_info else "Unbekanntes Medikament"
            
            scan_data_obj = ScanData(
                pzn=pzn,
                medication_name=med_name,
                expiry_date=parsed_data["expiry_date"],
                batch_lot=parsed_data["batch_lot"],
                serial_number=parsed_data["serial_number"],
                refill_link=generate_refill_link(pzn)
            )
            
            # Send Push Notification to Home Assistant in the background
            background_tasks.add_task(push_scan_to_homeassistant, scan_data_obj)
            
            return ScanResponse(
                success=True,
                source=source,
                data=scan_data_obj
            )
        
    if raw_barcode:
        try:
            # Parse den GS1 String
            parsed_data = dummy_gs1_parser(raw_barcode)
            pzn = parsed_data["pzn"]
            
            # PZN Validierung (Modulo 11)
            if not is_valid_pzn(pzn):
                # Wenn ungültig, könnten wir theoretisch OCR triggern, aber hier für den Test brechen wir ab
                raise HTTPException(status_code=400, detail=f"Ungültige PZN aus Barcode extrahiert: {pzn}")
                
            # Datenbank Lookup (Mock)
            med_info = lookup_pzn(pzn)
            if not med_info:
                med_name = "Unbekanntes Medikament (PZN nicht in lokaler DB)"
            else:
                med_name = med_info["name"]
                
            scan_data_obj = ScanData(
                pzn=pzn,
                medication_name=med_name,
                expiry_date=parsed_data["expiry_date"],
                batch_lot=parsed_data["batch_lot"],
                serial_number=parsed_data["serial_number"],
                refill_link=generate_refill_link(pzn)
            )
            
            # Send Push Notification to Home Assistant in the background
            background_tasks.add_task(push_scan_to_homeassistant, scan_data_obj)
            
            return ScanResponse(
                success=True,
                source=source,
                data=scan_data_obj
            )
            
        except Exception as e:
            return ScanResponse(
                success=False,
                source="error",
                error=str(e)
            )
            
    return ScanResponse(
        success=False,
        source="none",
        error="Weder 'raw_barcode' noch 'image' wurden übermittelt."
    )

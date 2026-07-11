import re
from typing import Optional, Dict, Any
from fastapi import HTTPException

from auramed.core.database import lookup_pzn
from auramed.core.pzn_validator import is_valid_pzn
from auramed.core.date_math import parse_gs1_expiry_date
from auramed.core.decoder import decode_datamatrix_from_bytes
from auramed.core.ocr import run_ocr_extraction
from auramed.core.image_utils import convert_to_jpeg_bytes
from auramed.models import ScanResponse, ScanData
from auramed.core.affiliate import generate_refill_link

def parse_gs1_barcode(barcode: str) -> Dict[str, str]:
    """
    Parst einen GS1 DataMatrix String in PZN, Verfallsdatum, Charge und Seriennummer.
    """
    gtin_match = re.search(r'\(?01\)?(\d{14})', barcode)
    exp_match = re.search(r'\(?17\)?(\d{6})', barcode)
    batch_match = re.search(r'\(?10\)?([A-Za-z0-9]+)', barcode)
    serial_match = re.search(r'\(?21\)?([A-Za-z0-9]+)', barcode)

    if not (gtin_match and exp_match and batch_match and serial_match):
        raise ValueError("Barcode enthält nicht alle erforderlichen GS1 AIs (01, 17, 10, 21)")

    gtin = gtin_match.group(1)
    pzn = gtin[5:13] # Deutsche NTINs
    
    exp_date = parse_gs1_expiry_date(exp_match.group(1))

    return {
        "pzn": pzn,
        "expiry_date": exp_date,
        "batch_lot": batch_match.group(1),
        "serial_number": serial_match.group(1)
    }

async def process_scan(raw_barcode: Optional[str], image_bytes: Optional[bytes]) -> ScanResponse:
    """
    Zentrale Logik für die Verarbeitung eines Scans (entweder über Barcode-String oder Bild-Upload).
    Verwendet OCR-Fallback, falls das Bild keinen lesbaren Datamatrix-Code enthält.
    """
    source = "datamatrix"

    if image_bytes:
        image_bytes = convert_to_jpeg_bytes(image_bytes)
        
        # 1. Datamatrix decodieren
        raw_barcode = decode_datamatrix_from_bytes(image_bytes)
        
        if raw_barcode:
            source = "datamatrix_image"
        else:
            # 2. OCR Fallback
            source = "ocr_fallback"
            ocr_data = run_ocr_extraction(image_bytes)
            pzn = ocr_data.get("pzn")
            
            if not pzn:
                return ScanResponse(
                    success=False,
                    source=source,
                    error="Kein DataMatrix Code gefunden und OCR konnte keine PZN extrahieren."
                )
                
            if not is_valid_pzn(pzn):
                raise HTTPException(status_code=400, detail=f"Ungültige PZN aus OCR extrahiert: {pzn}")
                
            med_info = lookup_pzn(pzn)
            med_name = med_info["name"] if med_info else "Unbekanntes Medikament"
            
            scan_data_obj = ScanData(
                pzn=pzn,
                medication_name=med_name,
                expiry_date=ocr_data.get("expiry_date", "Unbekannt"),
                batch_lot="Unbekannt (OCR)",
                serial_number="Unbekannt (OCR)",
                refill_link=generate_refill_link(pzn)
            )
            
            return ScanResponse(success=True, source=source, data=scan_data_obj)
            
    if raw_barcode:
        try:
            parsed_data = parse_gs1_barcode(raw_barcode)
            pzn = parsed_data["pzn"]
            
            if not is_valid_pzn(pzn):
                raise HTTPException(status_code=400, detail=f"Ungültige PZN aus Barcode extrahiert: {pzn}")
                
            med_info = lookup_pzn(pzn)
            med_name = med_info["name"] if med_info else "Unbekanntes Medikament (PZN nicht in lokaler DB)"
                
            scan_data_obj = ScanData(
                pzn=pzn,
                medication_name=med_name,
                expiry_date=parsed_data["expiry_date"],
                batch_lot=parsed_data["batch_lot"],
                serial_number=parsed_data["serial_number"],
                refill_link=generate_refill_link(pzn)
            )
            
            return ScanResponse(success=True, source=source, data=scan_data_obj)
            
        except Exception as e:
            return ScanResponse(success=False, source="error", error=str(e))
            
    return ScanResponse(
        success=False,
        source="none",
        error="Weder 'raw_barcode' noch 'image' wurden übermittelt."
    )

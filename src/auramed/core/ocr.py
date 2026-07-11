import re
from typing import Optional, Dict

try:
    from google.cloud import vision
    VISION_AVAILABLE = True
except Exception:
    # Fallback für lokales Testing auf Macs mit Python 3.14 (Protobuf Bug)
    VISION_AVAILABLE = False
    print("Warnung: google.cloud.vision konnte nicht geladen werden. OCR-Fallback ist lokal deaktiviert.")
    vision = None

def run_ocr_extraction(image_bytes: bytes) -> Dict[str, Optional[str]]:
    """
    Extracts text from an image using Google Cloud Vision API.
    Attempts to find:
    - PZN (format: PZN followed by 8 digits)
    - Expiry Date (EXP or Verwendbar bis)
    
    Returns a dictionary with extracted fields (if found).
    """
    if vision is None:
        return {"pzn": None, "expiry_date": None, "raw_text": "OCR lokal deaktiviert wegen Python 3.14 Inkompatibilität."}

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)
    
    # Perform document text detection (better for dense text like on packaging)
    response = client.document_text_detection(image=image)
    
    if response.error.message:
        raise Exception(f"Vision API Error: {response.error.message}")
        
    full_text = response.full_text_annotation.text
    if not full_text:
        return {"pzn": None, "expiry_date": None, "raw_text": None}
        
    extracted_data = {
        "pzn": None,
        "expiry_date": None,
        "raw_text": full_text
    }
    
    # Simple regex to find PZN
    # Examples: PZN: 12345678, PZN - 12345678, PZN 12345678, PZN12345678
    pzn_match = re.search(r'PZN[\s:\-]*(\d{8})', full_text, re.IGNORECASE)
    if pzn_match:
        extracted_data["pzn"] = pzn_match.group(1)
        
    # Simple regex to find Expiry Date
    # Examples: EXP: 12/2028, EXP 05-28, Verw. bis: 12/2028
    exp_match = re.search(r'(?:EXP|Verw\.?\s*bis)[\s:\-]*(\d{2}[\/\-]\d{2,4})', full_text, re.IGNORECASE)
    if exp_match:
        extracted_data["expiry_date"] = exp_match.group(1)
        
    return extracted_data

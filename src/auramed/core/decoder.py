import cv2
import numpy as np
from pylibdmtx.pylibdmtx import decode
from typing import Optional

def decode_datamatrix_from_bytes(image_bytes: bytes) -> Optional[str]:
    """
    Decodes a GS1 DataMatrix from raw image bytes.
    Uses OpenCV to load the image and pylibdmtx to decode it.
    Returns the decoded raw string if found, else None.
    """
    # Convert raw bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    
    # Decode image
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Could not decode image from bytes.")
        
    # Convert to grayscale to improve decoding chances
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Decode using pylibdmtx
    results = decode(gray)
    
    if results:
        # Assuming the first found matrix is the correct one.
        # GS1 DataMatrix strings typically use FNC1 characters.
        # We decode as utf-8, ignoring non-decodable characters or replacing them.
        barcode_data = results[0].data.decode('utf-8', errors='ignore')
        return barcode_data
        
    return None

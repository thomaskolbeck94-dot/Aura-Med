import io
from PIL import Image
import pillow_heif

# Registriere HEIF support in Pillow
pillow_heif.register_heif_opener()

def convert_to_jpeg_bytes(image_bytes: bytes) -> bytes:
    """
    Konvertiert ein beliebiges Bild (inkl. HEIC) in JPEG-Bytes.
    Dies stellt sicher, dass OpenCV und Google Cloud Vision die Bilder lesen können.
    """
    try:
        # Lade das Bild aus dem Bytes-Stream (unterstützt HEIC durch register_heif_opener)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Konvertiere nach RGB, falls es einen Alpha-Kanal gibt (z.B. PNG) oder es HEIC ist
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Verkleinere das Bild, wenn es riesig ist (z.B. 4000x3000 vom iPhone)
        # pylibdmtx friert bei solchen Auflösungen oft sekunden- oder minutenlang ein.
        max_size = (1000, 1000)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
        # Speichere als JPEG in einen neuen Byte-Stream
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=95)
        
        return output.getvalue()
    except Exception as e:
        # Falls die Konvertierung fehlschlägt, geben wir die Original-Bytes zurück
        # oder werfen einen Fehler.
        print(f"Warnung: Bildkonvertierung fehlgeschlagen: {str(e)}")
        return image_bytes

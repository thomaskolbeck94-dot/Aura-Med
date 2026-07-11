import os
import json
import urllib.request
import urllib.error
from auramed.models import ScanData

# Home Assistant Webhook URL (sollte als Environment Variable gesetzt werden)
HA_WEBHOOK_URL = os.environ.get("HA_WEBHOOK_URL", "")

def push_scan_to_homeassistant(scan_data: ScanData):
    """
    Sendet einen Webhook an Home Assistant, wenn ein Medikament gescannt wird.
    Home Assistant kann diesen Webhook nutzen, um eine Benachrichtigung oder eine Lovelace-Card zu erstellen.
    """
    if not HA_WEBHOOK_URL:
        # Wenn keine URL konfiguriert ist, brechen wir ab (z.B. im lokalen Test-Modus)
        print("INFO: Home Assistant Webhook URL nicht konfiguriert. Überspringe Push.")
        return

    payload = {
        "event_type": "auramed_medication_scanned",
        "medication": {
            "pzn": scan_data.pzn,
            "name": scan_data.medication_name,
            "expiry_date": scan_data.expiry_date,
            "batch": scan_data.batch_lot,
            "refill_link": scan_data.refill_link
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(HA_WEBHOOK_URL, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        urllib.request.urlopen(req, timeout=5)
        print(f"SUCCESS: Webhook an Home Assistant gesendet für {scan_data.medication_name}")
    except urllib.error.URLError as e:
        print(f"ERROR: Home Assistant Webhook fehlgeschlagen - {e.reason}")

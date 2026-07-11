# AuraMed MCP Server

Der AuraMed MCP (Model Context Protocol) Server ist die Schnittstelle für KI-Agenten und LLMs, um direkt mit der AuraMed-Logik zu interagieren. Er ermöglicht es externen Tools, Medikamentenverpackungen zu scannen, OCR durchzuführen und Stammdaten aus der PZN-Datenbank abzurufen.

## Tools (Werkzeuge)

Der MCP Server stellt aktuell 3 Tools zur Verfügung:

### 1. `scan_datamatrix`
Liest einen GS1-DataMatrix Code aus einem Bild aus.
- **Input:** `image_base64` (Das Bild der Verpackung, base64-kodiert).
- **Output:** Der reine GS1-String oder eine Fehlermeldung, falls kein Code gefunden wurde.

### 2. `run_ocr_extraction`
Führt eine optische Texterkennung (OCR) über die Google Cloud Vision API aus, falls der DataMatrix-Code nicht lesbar ist. Erkennt Ablaufdatum und PZN im Klartext.
- **Input:** `image_base64` (Das Bild der Verpackung, base64-kodiert).
- **Output:** Ein JSON-Objekt mit `pzn`, `expiry_date` und dem kompletten erkannten Roh-Text (`raw_text`).
- **Hinweis:** Bei lokalen Tests auf Python 3.14+ (macOS) wird dies automatisch deaktiviert, um Inkompatibilitäten mit der C-Erweiterung von `protobuf` zu vermeiden.

### 3. `lookup_pzn_database`
Prüft eine PZN (Pharmazentralnummer) lokal und reichert sie mit Datenbankinformationen (wie z.B. dem Namen des Medikaments) an.
- **Input:** `pzn` (Die 8-stellige PZN als String).
- **Output:** JSON mit Medikamenten-Stammdaten und einem generierten Refill-Link (Affiliate-Link). Führt zudem einen Modulo-11 Check auf die PZN aus und blockiert ungültige Nummern.

## Architektur & Ausführung
- Der Server wird via `mcp.server.stdio_server` gestartet und kommuniziert über Standard-In/Out.
- Um den Server lokal zu testen, kann das bereitgestellte Skript `test_mcp_client.py` verwendet werden:
  ```bash
  source .venv/bin/activate
  PYTHONPATH=src python test_mcp_client.py
  ```
- Benötigt lokal die Bibliothek `libdmtx` für den Barcode-Scan (auf dem Mac installierbar via `brew install libdmtx`).

## Integration
Agenten, die das Model Context Protocol unterstützen (wie z.B. Claude Desktop), können direkt an diesen Server angebunden werden, um Medikamente automatisch für den Benutzer zu scannen und auszuwerten.

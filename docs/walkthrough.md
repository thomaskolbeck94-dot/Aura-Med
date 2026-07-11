# Walkthrough: AuraMed Bildverarbeitung & MCP-Server

In diesem Ausbauschritt haben wir die "Augen" von AuraMed implementiert: Die Bilderkennungspipeline sowie den Antigravity Model Context Protocol (MCP) Server, der diese Fähigkeiten den Agenten bereitstellt.

## 1. DataMatrix Bild-Dekoder (`pylibdmtx`)

In [`src/auramed/core/decoder.py`](file:///Users/thomaskolbeck/Kolbeck%20Digital/Unitera.io/AuraMed/src/auramed/core/decoder.py) haben wir die Funktion `decode_datamatrix_from_bytes` implementiert. 
- **OpenCV** liest den rohen Byte-Stream der Bilddatei direkt in den Arbeitsspeicher und konvertiert ihn für höhere Kontraste in Graustufen.
- **pylibdmtx** extrahiert dann den securPharm GS1-String aus dem DataMatrix-Code.

## 2. OCR-Fallback (`google-cloud-vision`)

Für unleserliche, beschädigte oder überklebte Verpackungen greift [`src/auramed/core/ocr.py`](file:///Users/thomaskolbeck/Kolbeck%20Digital/Unitera.io/AuraMed/src/auramed/core/ocr.py). 
- Nutzt die **Google Cloud Vision API** (`document_text_detection` ist speziell für dichte Texte optimiert).
- Enthält intelligente reguläre Ausdrücke (Regex), um gängige PZN-Muster (z.B. "PZN 12345678", "PZN: 12345678") und Ablaufdaten (z.B. "EXP: 12/2028") völlig flexibel aus dem Verpackungstext zu "fischen".

## 2. BfArM-konformes Relationales SQLite-Schema

Wir haben die Datenbank (`core/database.py`) nach dem offiziellen Datenmodell des **Forschungsdatenzentrums Gesundheit (BfArM)** auf ein 3-Tabellen-Modell umgeschrieben:
1. **`REFERENCE_MEDICINAL_PRODUCT` (RMP):** Speichert die Zulassungsbezeichnungen der Fertigarzneimittel (Primary Key: PZN).
2. **`REFERENCE_PHARMACEUTICAL_PRODUCT` (RPP):** Speichert die einzelnen Komponenten einer Packung (wichtig für Kombipräparate).
3. **`REFERENCE_SUBSTANCE` (RSE):** Speichert die atomaren Wirkstoffe pro Komponente.

> [!TIP]
> **Performance & Automation:** Wir haben eine Funktion `import_dsv_data()` implementiert, die das offizielle Pipe-getrennte (DSV) Format des BfArM liest und extrem schnell über `INSERT OR REPLACE` in die Datenbank schreibt. Damit ist die Applikation perfekt für automatische 14-tägige Updates über z. B. n8n vorbereitet!

Die Abfrage-Funktion `lookup_pzn` wurde so umgebaut, dass sie per SQL `JOIN` alle Wirkstoffe eines Medikaments für die API-Ausgabe zusammenfasst.

## 3. Integration in die FastAPI-Routen

Der bestehende Endpunkt `POST /api/v1/scan` wurde in [`src/auramed/api.py`](file:///Users/thomaskolbeck/Kolbeck%20Digital/Unitera.io/AuraMed/src/auramed/api.py) massiv erweitert. 
- Lädt ein Nutzer nun eine Bilddatei über das Formularfeld `image` hoch, versucht die API **zuerst** den blitzschnellen, lokalen DataMatrix-Decoder.
- **Nur bei einem Fehler** (Fallback) wird das Bild an die Cloud-OCR gesendet.
- Die aus dem Bild extrahierten Rohdaten (PZN, Ablaufdatum) fließen direkt durch unseren *Modulo-11-Validator* und die *SQLite-Stammdatenbank*.

> [!TIP]
> Diese zweistufige Pipeline (Lokal First $\rightarrow$ Cloud Fallback) ist der Schlüssel zu einem perfekten Kompromiss aus Datenschutz, niedrigen API-Kosten und maximaler Ausfallsicherheit.

## 4. Der Antigravity MCP-Server

Um AuraMed als echtes Antigravity-Plugin betreiben zu können, haben wir den Model Context Protocol Server in [`src/auramed/mcp_server.py`](file:///Users/thomaskolbeck/Kolbeck%20Digital/Unitera.io/AuraMed/src/auramed/mcp_server.py) implementiert.

Er läuft als `stdio`-Prozess (Standard Input/Output), was maximale Sicherheit garantiert, da keine lokalen Netzwerkports (HTTP/WebSocket) freigegeben werden müssen. Er exponiert genau drei Tools für Antigravity-Agenten:
1. `scan_datamatrix`
2. `run_ocr_extraction`
3. `lookup_pzn_database`

> [!IMPORTANT]
> Der Agent kann jetzt einen base64-kodierten Bild-String über diese Tools einspeisen und erhält sofort das strukturierte Ergebnis zurück. Genau darauf verweist die `mcp_config.json`, die wir in Schritt 1 angelegt haben!

## 5. Dockerisierung (Local-First Deployment)

Damit AuraMed portabel ist und sofort bei Endkunden oder auf Home-Servern ausgerollt werden kann, haben wir ein **`Dockerfile`** erstellt.
- **Basis:** `python:3.12-slim` (minimaler Footprint).
- **System-Libraries:** Installiert `libdmtx0a` nativ in den Container, damit der `pylibdmtx` Decoder fehlerfrei kompilieren und arbeiten kann.
- **Daten-Persistenz:** Wir haben einen dedizierten Ordner `/app/data/` im Container angelegt, in den die SQLite-Datenbank geschrieben wird. Dies erlaubt es, die Datenbank über ein Docker-Volume an den Host zu binden, um Datenverlust beim Container-Neustart zu vermeiden.
- **Run-Kommando:** Der Container startet standardmäßig den `uvicorn` Webserver und gibt Port `8000` frei.

## 6. Smart Refill (Affiliate Monetarisierung - Säule 3)

Wir haben den strategischen Baustein für das **Smart Refill Geschäftsmodell** implementiert:
- **`affiliate.py`:** Sobald ein Medikament erkannt wird, generiert AuraMed vollautomatisch einen provisionsfähigen Refill-Link (aktuell als Beispiel für *Shop-Apotheke* oder *DocMorris*).
- **Die Logik:** Der Algorithmus nutzt die exakte PZN, um eine Such- oder Warenkorb-URL inklusive Ihrer Affiliate-ID zusammenzubauen (z. B. `https://www.shop-apotheke.com/search.htm?i={pzn}&affiliate=auramed`).
- **Integration:** Dieser Link wird ab sofort bei jeder Erkennung als `refill_link` im JSON der FastAPI und im MCP-Server an Drittanwendungen (wie Home Assistant) mitgeschickt.

> [!TIP]
> **Der USP in Aktion:** Da Home Assistant über AuraMed genau weiß, wann das Medikament abläuft, kann es dem Nutzer 14 Tage vorher eine Notification senden: *"Ihr Aspirin Complex läuft bald ab. Hier mit einem Klick nachbestellen: [Link]"*. Das konvertiert extrem stark!

## 7. Home Assistant Integration (Zero-UI Push-Benachrichtigungen)

Um dem "Zero-UI"-Gedanken treu zu bleiben, haben wir AuraMed so programmiert, dass es selbst kein Dashboard braucht, sondern sich direkt in Smart-Home-Systeme einklinkt:
- **`homeassistant.py`:** Ein Modul, das einen HTTP-Webhook (JSON-Payload) an Home Assistant sendet, sobald ein Medikament verarbeitet wurde. Die Payload enthält alle Daten (Name, Ablaufdatum, Charge, Seriennummer) und natürlich den generierten `refill_link`.
- **Background Tasks:** In der FastAPI-Route wird dieser Webhook als **Background Task** ausgeführt. Das heißt, die API wartet nicht auf die Antwort von Home Assistant, sondern antwortet dem Nutzer (oder dem Antigravity-Agenten) sofort. Die Push-Benachrichtigung wird geräuschlos und asynchron im Hintergrund verschickt.
- **Konfiguration:** Die Webhook-URL kann einfach über die Umgebungsvariable `HA_WEBHOOK_URL` in das System gegeben werden (z. B. `http://homeassistant.local:8123/api/webhook/auramed_scan`).

---

Damit ist die komplette Pipeline aus dem Projektplan (Architektur, Logik, API, MCP-Plugin, Docker, Smart Refill und Home Assistant Webhooks) technisch aufgesetzt und für den Betrieb bereit!

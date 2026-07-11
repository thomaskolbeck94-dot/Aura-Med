# AuraMed - Open Core

AuraMed ist eine intelligente Medikamenten-API, die das Einscannen und Verwalten der Hausapotheke für Smart Home Anwendungen extrem vereinfacht. Sie kombiniert einen lokalen GS1-Datamatrix Scanner mit einer BfArM-konformen PZN-Auswertung.

Dieses Repository enthält den "Open Core" des Projekts und ist speziell darauf ausgelegt, als **MCP (Model Context Protocol) Server** für Agenten (wie Claude oder Cursor) oder als lokale Docker-Instanz betrieben zu werden.

## Features
- **GS1 Datamatrix Parsing:** Entschlüsselt Haltbarkeitsdaten, Chargen und PZN lokal in Millisekunden.
- **BfArM-Validierung:** Erkennt deutsche Medikamente anhand der PZN (Pharmazentralnummer).
- **OCR Fallback (Optional):** Lese unleserliche Codes direkt aus den Bildpixeln über die Google Cloud Vision API.
- **MCP-Plugin Ready:** Kann nahtlos als Tool in LLM-Agenten eingebunden werden.

## Setup & Starten

### Lokales Ausführen (Ohne Docker)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Starten des FastAPI Servers
uvicorn src.auramed.api:app --reload
```

### Starten via Docker
```bash
docker compose up -d --build
```

## Konfiguration (.env)
Kopiere die `.env.example` zu `.env`:
```bash
cp .env.example .env
```
Standardmäßig ist `REQUIRE_API_KEY=false`, sodass du den Service lokal ohne Authentifizierung nutzen kannst.

## MCP (Model Context Protocol)
AuraMed kann als MCP-Server eingebunden werden, um Agenten beizubringen, wie sie Medikamentenfotos analysieren.

Beispiel `mcp_config.json` (wird in deiner Cursor/Claude Config eingetragen):
```json
{
  "mcpServers": {
    "auramed-core": {
      "command": "python",
      "args": ["-m", "auramed.mcp_server"]
    }
  }
}
```
Die detaillierten Skills und Guidelines findest du im Ordner `auramed-plugin/`.

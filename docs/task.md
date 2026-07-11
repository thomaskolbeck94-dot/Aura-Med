- [x] Refaktorierung des SQLite-Schemas auf das BfArM-Referenzkatalog-Modell (`REFERENCE_MEDICINAL_PRODUCT`, `PHARMACEUTICAL_PRODUCT`, `SUBSTANCE`) in `core/database.py`.
- [x] Implementierung einer DSV (Pipe `|`) Import-Funktion mittels `INSERT OR REPLACE`.
- [x] Anpassung der Funktion `lookup_pzn` zur Aggregation der 3 Tabellen über SQL `JOIN`.
- [x] Migration der Mock-Daten in das neue DSV-Format.
- [x] Aktualisierung des Walkthrough-Artefakts.

---
- [x] Erstelle das `Dockerfile` für das zustandslose Local-First Deployment.
- [x] Aktualisiere den Walkthrough.

---
- [x] Erstelle Affiliate-Link Generator (`src/auramed/core/affiliate.py`).
- [x] Erweitere API Response Modelle um `refill_link` (`src/auramed/models.py` & `src/auramed/api.py`).
- [x] Aktualisiere den Antigravity MCP Server (`src/auramed/mcp_server.py`).
- [x] Aktualisiere den Walkthrough.

---
- [x] Erstelle Webhook-Logik für Home Assistant (`src/auramed/core/homeassistant.py`).
- [x] Integriere Home Assistant Push-Benachrichtigungen als Background Task in FastAPI (`src/auramed/api.py`).
- [x] Aktualisiere den Walkthrough.

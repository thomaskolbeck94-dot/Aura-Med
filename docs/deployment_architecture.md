# AuraMed Systemarchitektur & Deployment

Dieses Dokument beschreibt die technische Live-Architektur von AuraMed auf dem Hetzner-Server, Stand heute.

---

## Übersicht der Infrastruktur

AuraMed wird als Headless-API betrieben. Die Infrastruktur liegt auf einem dedizierten Hetzner CX22 Cloud-Server und wird über Docker orchestriert. Der eingehende Traffic wird über All-Inkl DNS an den Server geleitet und dort vom Nginx Proxy Manager sicher (via Let's Encrypt SSL) an die jeweiligen Container verteilt.

```mermaid
graph TD
    classDef external fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px;
    classDef server fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px;
    classDef container fill:#e3f2fd,stroke:#1976d2,stroke-width:2px;
    classDef db fill:#fff3e0,stroke:#f57c00,stroke-width:2px;

    User[Endnutzer / Entwickler]:::external
    Stripe[Stripe Webhook]:::external
    DNS[All-Inkl DNS]:::external

    User -->|Aufruf URL| DNS
    Stripe -->|Zahlung bestätigt| DNS

    DNS -->|Leitet an IP 178.104.29.255| Server[Hetzner CX22 Ubuntu Server]:::server

    subgraph Server [Hetzner Server (178.104.29.255)]
        NPM[Nginx Proxy Manager\nPort 80/443]:::container
        
        NPM -->|api.getauramed.de| API[FastAPI Backend\nPort 8000]:::container
        NPM -->|getauramed.de| Web[Landingpage Nginx\nPort 8080]:::container
        
        API <--> SQLite[(SQLite Datenbank\n/data/auramed.db)]:::db
    end
```

## Komponenten

### 1. DNS & Domain (All-Inkl KAS)
- **Hauptdomain (`getauramed.de`)**: Zeigt per `A`-Record auf die Hetzner-IP `178.104.29.255`.
- **API-Subdomain (`api.getauramed.de`)**: Zeigt ebenfalls per `A`-Record auf die Hetzner-IP.

### 2. Nginx Proxy Manager (NPM)
Der NPM verwaltet die eintreffenden Anfragen und sorgt für die automatische Ausstellung von **Let's Encrypt SSL-Zertifikaten**.
- Leitet Traffic für `getauramed.de` an den Docker-Container `auramed-frontend` (Port 8080) weiter.
- Leitet Traffic für `api.getauramed.de` an den Docker-Container `auramed-api` (Port 8000) weiter.

### 3. Docker Compose (`docker-compose.yml`)
Das Projekt läuft in zwei schlanken Containern:
- **`api`**: Baut das Python/FastAPI-Image aus dem lokalen Code. Enthält die GS1-Erkennung, Stripe-Logik und API-Key Generierung.
- **`frontend`**: Ein leichtgewichtiger `nginx:alpine` Container, der die statischen HTML/CSS/JS-Dateien der Landingpage aus dem `/web` Ordner ausliefert.

### 4. Datenbank (`database.py`)
- **System**: SQLite (lokal, schnell, leicht zu sichern).
- **Speicherort**: Der Ordner `data/` wird als Volume (persistenter Speicher) aus dem Container auf den Host-Server gemappt, damit die Daten bei einem Container-Neustart nicht verloren gehen.

### 5. Payment & API-Key Flow (Stripe)
1. Nutzer kauft über den Stripe-Checkout-Link auf der Landingpage.
2. Stripe sendet einen POST-Request an `https://api.getauramed.de/api/v1/stripe/webhook`.
3. FastAPI verifiziert die Stripe-Signatur (über `.env` Keys).
4. Das Backend generiert einen sicheren API-Key (z.B. `aura_sk_...`) und speichert ihn in der SQLite-Datenbank ab.
5. (Geplant): n8n wird angebunden, um eine Willkommens-Mail mit dem Key zu versenden.

## Wichtige Befehle für die Wartung
Wenn am Code gearbeitet wurde, wird das Update wie folgt auf den Live-Server gespielt:
```bash
# 1. Änderungen per SCP hochladen
scp -r src/ web/ docker-compose.yml requirements.txt root@178.104.29.255:/opt/auramed/

# 2. Auf dem Server neu bauen und starten
docker compose up -d --build
```

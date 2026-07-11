# 1. Basis-Image: Leichtgewichtiges Python 3.11 (Debian Slim)
FROM python:3.11-slim

# 2. Umgebungsvariablen setzen
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
# Pfad für die SQLite Datenbank (Standardmäßig lokal im Container, kann über Volume gemounted werden)
ENV AURAMED_DB_PATH=/app/data/auramed.db

# 3. Arbeitsverzeichnis erstellen
WORKDIR /app

# 4. System-Abhängigkeiten installieren (wichtig für pylibdmtx und OpenCV)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libdmtx0b \
    && rm -rf /var/lib/apt/lists/*

# 5. Python-Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Quellcode in den Container kopieren
COPY src/ /app/src/

# 7. Daten-Verzeichnis für SQLite erstellen
RUN mkdir -p /app/data

# 8. Port für die FastAPI Anwendung freigeben
EXPOSE 8000

# 9. Startkommando: FastAPI mit Uvicorn
CMD ["uvicorn", "auramed.api:app", "--host", "0.0.0.0", "--port", "8000"]

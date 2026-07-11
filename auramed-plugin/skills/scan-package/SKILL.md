---
name: scan-package
description: Verarbeitet ein Foto oder einen rohen Scan-String einer Medikamentenschachtel und extrahiert GS1-konforme Metadaten.
---

# Handlungsanweisungen für den Agenten bei Aufruf von /scan-package

## 1. Eingabe erfassen
Nimm das vom Benutzer bereitgestellte Bild der Medikamentenpackung oder den manuell eingelesenen Barcode-String entgegen.

## 2. Datenextraktion
- Versuche, über das angeschlossene MCP-Tool `scan_datamatrix` den GS1-Code auszulesen.
- Falls kein DataMatrix-Code gefunden wird oder der Scan fehlerhaft ist, triggere das Tool `run_ocr_extraction`, um das gedruckte Datum und den Namen optisch zu erfassen.

## 3. Validierung
- Wende die Monatsende-Logik an, falls das Ablaufdatum auf 00 endet (siehe Monatsende-Ablaufdatum-Algorithmus in `rules/auramed-guidelines.md`).
- Löse die PZN (Pharmazentralnummer) über das MCP-Tool `lookup_pzn_database` auf, um den Medikamentennamen und Sicherheitswarnungen zu ergänzen.

## 4. Ausgabe erzeugen
Gib das Ergebnis als formatiertes JSON-Dokument zurück und erstelle einen optischen Statusbericht (grün/gelb/rot) für den Benutzer.

# Implementierungsplan: BfArM-konformes SQLite Schema

Dieser Plan beschreibt das Refactoring unserer SQLite-Datenbank (`src/auramed/core/database.py`). Anstelle einer flachen `medications`-Tabelle migrieren wir auf das offizielle 3-Tabellen-Modell des BfArM (Bundesinstitut für Arzneimittel und Medizinprodukte). 

## 🚨 Open Questions (Offene Fragen zur Klärung)

> [!IMPORTANT]
> **Mock-Daten Migration:** Da wir die eRezept-Beispiele (z. B. *Aspirin Complex*) weiterhin als Mock-Daten nutzen, werde ich die bestehenden Dummy-Werte so umschreiben, dass sie sich korrekt in die drei neuen Tabellen (Produkt, Komponente, Wirkstoff) aufteilen. Sind Sie einverstanden, dass ich dafür eine saubere Import-Funktion (`INSERT OR REPLACE`) schreibe, die die Pipe-getrennte (DSV) Logik bereits für künftige n8n-Imports simuliert?

---

## 🏗️ Proposed Changes (Geplante Architektur)

Das Modul `src/auramed/core/database.py` wird komplett umgeschrieben.

### [MODIFY] [database.py](file:///Users/thomaskolbeck/Kolbeck%20Digital/Unitera.io/AuraMed/src/auramed/core/database.py)

#### Neue Tabellenstruktur (Referenzkatalog):
1. **`REFERENCE_MEDICINAL_PRODUCT` (RMP)**
   - Beinhaltet die Stammdaten des Fertigarzneimittels.
   - `RMP_KEY` als Primary Key (entspricht der PZN).
   - Enthält Zulassungsbezeichnung (`RMP_MPD_NAME`), Darreichungsformen (`RMP_PFM_PUT_SHORT`), etc.
2. **`REFERENCE_PHARMACEUTICAL_PRODUCT` (RPP)**
   - Beinhaltet die Komponenten einer Packung (wichtig für Kombipackungen).
   - `RPP_KEY` als PK (`<PZN>-<Nummer>`).
   - `RMP_KEY` als Foreign Key auf RMP.
3. **`REFERENCE_SUBSTANCE` (RSE)**
   - Beinhaltet die atomaren Wirkstoffe pro Komponente.
   - `RSE_KEY` als PK (`<PZN>-<Komponente>-<Rang>`).
   - `RPP_KEY` als Foreign Key auf RPP.
   - Enthält Wirkstoffname (`RSE_SUBSTANCE_NAME`) und ID (`RSE_SUBSTANCE_ID`).

#### Anpassung der PZN-Abfrage (`lookup_pzn`):
Die Funktion `lookup_pzn(pzn)` wird einen SQL `JOIN` ausführen, um aus den drei Tabellen wieder ein kompaktes JSON-Dictionary für die FastAPI-Routen zusammenzubauen:
- Sie holt das RMP.
- Sie holt alle dazugehörigen Komponenten (RPP).
- Sie aggregiert alle Wirkstoffe (RSE) der Komponenten zu einer kommagetrennten Liste oder einem Array.

#### Beibehaltene Tabellen:
Die `inventory`-Tabelle bleibt als Verknüpfung bestehen, da AuraMed weiterhin die lokal gescannten Packungen (Batch, Serial, Expiry) der Endnutzer speichern muss.

## 🧪 Verification Plan
1. **Schema Check:** Verifizieren, dass die SQLite-Datenbank erfolgreich mit dem relationalen BfArM-Schema erstellt wird.
2. **Mock-Data Import Check:** Sicherstellen, dass die Mock-Daten korrekt (z.B. über `INSERT OR REPLACE`) auf alle 3 Tabellen verteilt werden.
3. **Lookup Check:** Sicherstellen, dass die `api.py` weiterhin das korrekte Medikament findet (die `JOIN`-Abfrage liefert die zusammengeführten Daten).

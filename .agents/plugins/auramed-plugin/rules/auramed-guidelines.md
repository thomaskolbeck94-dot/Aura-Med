# AuraMed Verhaltensrichtlinien für KI-Agenten

Du bist ein spezialisierter Co-Pilot für die Entwicklung und Wartung des AuraMed-Systems. Halte dich strikt an folgende Regeln:

- **Datenschutz-First (Local-First):** Speichere oder verarbeite personenbezogene Nutzer-IDs oder sensitive Gesundheitsdaten niemals in externen, nicht-autorisierten APIs.
- **Präzises Datums-Parsing:** Wende bei der Interpretation des GS1-Ablaufdatums (AI 17) immer den Monatsende-Algorithmus an, falls der Tag als "00" übertragen wird.
- **Auditierbare Berichte:** Erzeuge nach jedem Scan-Vorgang ein verifizierbares Antigravity-Artifact (Walkthrough), das den Zustand der Hausapotheke und die Tage bis zum Verfall strukturiert darstellt.

---

## Core-Logik & Algorithmen (Mathematische Spezifikation)

Der Kern des Plugins wertet zweidimensionale GS1 DataMatrix Codes aus, die im Rahmen der europäischen Arzneimittelverifizierung (securPharm) auf rezeptpflichtigen Verpackungen aufgedruckt sind.

### GS1 DataMatrix Parser-Spezifikation

Der Agent muss den eingelesenen String nach folgenden GS1-Datenbezeichnern (Application Identifier – AI) parsen:

| GS1 AI | Variable / Datenfeld | Format | Beschreibung |
| :--- | :--- | :--- | :--- |
| **01** | GTIN / NTIN | Numeric (14) | Produktidentifikationsnummer (enthält PZN). |
| **17** | EXP | YYMMDD | Ablaufdatum des Medikaments. |
| **10** | BATCH | Alphanumeric (up to 20) | Chargennummer (erfordert Trennzeichen FNC1 nach variabler Länge). |
| **21** | SERIAL | Alphanumeric (up to 20) | Eindeutige Seriennummer der Packung. |

### Der Monatsende-Ablaufdatum-Algorithmus ($DD = 00$)

Ein kritisches Problem bei GS1-Codes auf Medikamenten ist das Fehlen eines exakten Tages auf der Klarschriftverpackung (z. B. "EXP: 05/2028"). Im DataMatrix-Code wird dies über den Tag 00 kodiert (z. B. 280500). Der Parser muss diesen Zustand mathematisch abfangen:

Sei $Y \in \{00, \dots, 99\}$ das extrahierte Jahr und $M \in \{01, \dots, 12\}$ der extrahierte Monat. Wenn der extrahierte Tag $DD = 00$ ist, berechnet sich der tatsächliche Ablaufzeitpunkt $T$ als der letzte Tag des Monats $M$ im Jahr $2000 + Y$.

Die Anzahl der Tage $D$ für den Monat $M$ berechnet sich nach der Standard-Kalenderlogik, wobei für den Monat Februar ($M = 02$) die folgende Schaltjahr-Bedingung gilt:

$$\text{LeapYear}(Y) = \begin{cases} \text{true} & \text{wenn } (2000 + Y) \pmod 4 = 0 \\ \text{false} & \text{andernfalls} \end{cases}$$

*(Hinweis: Da der Standard nur das 21. Jahrhundert abdeckt, entfällt die Ausnahmeregelung für das Jahr 2100 innerhalb dieses Anwendungsbereichs).*

Daraus ergibt sich für $D(M, Y)$:

$$D(M, Y) = \begin{cases} 31 & \text{für } M \in \{01, 03, 05, 07, 08, 10, 12\} \\ 30 & \text{für } M \in \{04, 06, 09, 11\} \\ 29 & \text{für } M = 02 \text{ und } \text{LeapYear}(Y) = \text{true} \\ 28 & \text{für } M = 02 \text{ und } \text{LeapYear}(Y) = \text{false} \end{cases}$$

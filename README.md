# NK-Abrechnungsprogramm – Teinacher Str. 4, 75387 Neubulach

Nebenkosten- und Eigentümer-Abrechnung für ein Zweifamilienhaus mit
Wärmepumpe, getrennter Zählererfassung und mehreren Mietperioden.

Das Programm berechnet **alle Beträge aus den Roh-Zählerständen und den
Kostenparametern** – es sind keine Ergebnisse fest verdrahtet. Die
berechneten Summen reproduzieren die im Projekt dokumentierten
Abrechnungsergebnisse (centgenau bis auf Rundungsartefakte im
Ausgangsdokument, Toleranz ≤ 2 Cent).

## Objekt

| | |
|---|---|
| Adresse | Teinacher Str. 4, 75387 Neubulach |
| UG (vermietet) | 88 m² → **32,59 %** der Gesamtfläche |
| EG (Eigennutzung Christine) | 182 m² |
| Wärmeerzeugung | Luft-Wasser-Wärmepumpe (Mitsubishi) |

## Mietperioden

| Periode | Mieter | Zeitraum | Ergebnis |
|---|---|---|---|
| P1 | Felix Adameck | 02/2024 – 04/2025 | Nachzahlung **717,66 €** |
| Leerstand | (Thomas Weis) | 05/2025 – 07/2025 | von Thomas getragen **706,81 €** |
| P2 | Fam. Beltz | 08/2025 – 06/2026 | Nachzahlung **525,31 €** |

## Installation

```bash
pip install -r requirements.txt
```

## Nutzung

```bash
python main.py rechnen   # Ergebnisse in der Konsole
python main.py pdf       # alle PDFs nach ./output erzeugen
python main.py db        # SQLite-Datenbank aufbauen und seeden
python main.py alles     # DB + PDFs + Konsolenausgabe
```

Erzeugte Dateien in `output/`:

- `NK_Felix_Adameck.pdf` – Nebenkostenabrechnung P1
- `NK_Beltz_Abschluss.pdf` – Abschlussabrechnung P2 (inkl. 80 € Renovierung)
- `NK_Leerstand_Thomas.pdf` – Leerstandskosten
- `NK_Christine_Weis_Zwischenstand.pdf` – Eigentümer-interne Verrechnung
- `NK_Verbrauchsuebersicht.pdf` – Zählerstände + COP-Plausibilität
- `nk_teinacher.db` – SQLite-Datenbank mit Zählern, Ablesungen, Kosten, Zahlungen

## Projektstruktur

```
nk_abrechnung/
  config.py     Stammdaten, Zählerstände, Kostenparameter (einzige Datenquelle)
  engine.py     Berechnungslogik (Heizschlüssel, COP, Perioden-Abrechnung)
  database.py   SQLite-Schema und Seeding
  pdf.py        PDF-Erzeugung (ReportLab)
main.py         Kommandozeilen-Einstieg
tests/          Regressionstests gegen die dokumentierten Ergebnisse
```

## Berechnungsmethodik

**Heizschlüssel UG (`pug`)** – Anteil des UG an der Heizwärme, je Zählerperiode
direkt aus den Wärmemengenzähler-Deltas:

```
pug = ΔWMZ_UG / (ΔWMZ_UG + ΔWMZ_EG)
```

- P1 (Feb 2024 → Mai 2025): **46,60 %**
- Leer+P2 (Mai 2025 → Jun 2026): **68,89 %**

**COP-Plausibilitätsprüfung** – die März-2026-Ablesung der Wärmemengenzähler
wurde verworfen, weil sie ein falsches Register lieferte (COP 0,62 bzw. 7,94,
physikalisch unmöglich). Es wird nur mit den drei belastbaren Stichtagen
gerechnet; die Gesamtperiode ergibt einen plausiblen COP von 2,08.

**Leerstand-Split** – die Zählerperiode Mai 2025 → Jun 2026 (14 Monate) wird
aufgeteilt: Leerstand **3/14**, Beltz **11/14**.

**Heizkosten** = `WP_kWh_Anteil × pug × 0,2462 €/kWh`

**Warmwasser-Heizenergie** = `WW_m³ × 20,9 kWh/m³ × 0,2462 €/kWh` (= 5,14558 €/m³)

**Wasser/Niederschlag** – monatsgenau nach dem Tarif des jeweiligen
Kalenderjahres aufgeteilt.

## Kulanz Warmwasser EG

Der Warmwasser-Verbrauch der EG-Wohnung (Christine, Eigennutzung),
113,547 m³ ≈ **584,27 €**, wird von Thomas erlassen und fließt nicht in die
Verrechnung ein.

## Offene Punkte (Eigentümer-intern)

- Ab welchem Monat zahlt Thomas 240 €/Mon statt 195 €/Mon?
- Finale EnBW-Jahresrechnung 2025/26 zur Grundpreis-Verifizierung

## Tests

```bash
python -m pytest -q
```

Die Tests sichern ab, dass die Berechnung die dokumentierten Ergebnisse
(Felix 3.262,66 € SOLL, Beltz 3.110,31 €, Leerstand 706,81 €,
Heizschlüssel 46,60 % / 68,89 %, COP 2,08, WW-EG-Kulanz 584,27 €)
reproduziert.

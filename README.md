# NK-Abrechnungsprogramm – Teinacher Str. 4, 75387 Neubulach

Nebenkosten- und Eigentümer-Abrechnung für ein Zweifamilienhaus mit
Wärmepumpe, getrennter Zählererfassung und mehreren Mietperioden.

Das Programm berechnet **alle Beträge aus den Roh-Zählerständen und den
Kostenparametern** – es sind keine Ergebnisse fest verdrahtet. Die
berechneten Summen reproduzieren die im Projekt dokumentierten
Abrechnungsergebnisse (centgenau bis auf Rundungsartefakte im
Ausgangsdokument, Toleranz ≤ 2 Cent).

## 🔑 Übergabe an den neuen Eigentümer

Dieses Programm wird an den neuen Eigentümer des Objekts übergeben, der
künftig selbst im Haus wohnt und die laufende Abrechnung mit der zweiten
Partei (Christine Weis, Miteigentümerin) **lückenlos** fortführt. Ein
ausführliches PDF-Handbuch (`Handbuch_Uebergabe.pdf`) begleitet diese
Übergabe und erklärt Schritt für Schritt, wie die App eingerichtet und
genutzt wird – auch ohne Programmierkenntnisse.

- **Name des neuen Eigentümers:** aktuell Platzhalter
  `"Neuer Eigentümer (Name folgt)"` in `nk_abrechnung/config.py`
  (Konstante `NEUER_EIGENTUEMER_NAME`) – dort **einmal** eintragen, sobald
  bekannt; er erscheint danach automatisch überall in der App und in neuen
  PDFs.
- **Historische Abrechnungen** (Felix Adameck, Leerstand, Fam. Beltz bis zum
  Eigentümerwechsel) bleiben unverändert Thomas Weis zugeordnet, da sie in
  dessen Eigentumszeit fielen – sie werden nicht nachträglich umbenannt.
- **Geteilter Zugriff:** Damit beide Parteien jederzeit dieselben
  Zählerstände und Belege sehen und erfassen können, nutzt die App eine
  gemeinsame Cloud-Datenbank (Supabase/Postgres) statt einer lokalen Datei –
  siehe Abschnitt "☁️ Gemeinsamer Zugriff für beide Parteien" weiter unten.

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

### Kommandozeile

```bash
python main.py rechnen   # Ergebnisse in der Konsole
python main.py pdf       # alle PDFs nach ./output erzeugen
python main.py db        # SQLite-Datenbank aufbauen und seeden
python main.py alles     # DB + PDFs + Konsolenausgabe
```

### Streamlit-Oberfläche (Foto-Ablesung)

```bash
streamlit run streamlit_app.py
```

Die App bietet sechs Bereiche:

- **📷 Zähler ablesen** – Zähler wählen, Foto hochladen oder mit der Kamera
  aufnehmen; der Zählerstand wird per OCR vorgeschlagen und bestätigt. Ein
  Feld **"Erfasst von"** hält fest, wer die Ablesung gemacht hat. Eine
  Plausibilitätswarnung erscheint, wenn der neue Wert kleiner als die letzte
  Ablesung ist.
- **📋 Ablesungen** – Tabelle aller Ablesungen inkl. Foto-Vorschau und
  "Erfasst von" – für beide Parteien jederzeit einsehbar.
- **🗂️ Belege** – Foto-/PDF-Nachweise der Eingangsrechnungen (Strom, Wasser,
  Versicherung, Grundsteuer, Niederschlagswasser, Sonstiges) mit Lieferant,
  Betrag, Rechnungsdatum, Zeitraum und "Erfasst von". Praktisch, da viele
  Rechnungen bei der zweiten Partei eingehen – einmal hier erfasst, sind sie
  sofort für beide dokumentiert. Betrag wird bei Fotos per OCR vorgeschlagen;
  Übersicht mit Summen je Kategorie und Löschfunktion.
- **🧾 Abrechnung** – berechnete Ergebnisse je Partei mit PDF-Download.
- **📊 Verbrauch & COP** – Zählerstände und COP-Plausibilitätsprüfung.
- **ℹ️ Status** – Stammdaten, Kostenparameter, aktive OCR-Backends, aktives
  Datenbank-Backend.

### ☁️ Gemeinsamer Zugriff für beide Parteien (wichtig)

Damit **beide Parteien jederzeit, von jedem Gerät aus**, dieselben
Zählerstände und Belege sehen und ergänzen können, reicht die lokale
SQLite-Datei nicht aus – sie liegt nur auf einem Rechner und ist auf
Streamlit Cloud bei einem Neustart der App leer. Für echten, dauerhaften,
geteilten Zugriff wird eine **Postgres-Datenbank (kostenlos über Supabase)**
angebunden. Fotos und Beleg-Dateien werden dabei direkt in der Datenbank
gespeichert (nicht als lokale Datei), damit sie ebenfalls geteilt und
dauerhaft sind – vor dem Speichern werden sie automatisch verkleinert
(max. 1600 px, JPEG), damit der kostenlose Tarif ausreicht.

**Einrichtung (einmalig, ca. 5 Minuten):**

1. Kostenloses Projekt auf [supabase.com](https://supabase.com) anlegen.
2. Unter **Project Settings → Database → Connection string → URI** die
   Verbindungszeichenfolge kopieren (Format
   `postgresql://postgres:PASSWORT@db.XXXXX.supabase.co:5432/postgres`).
3. Diese Zeichenfolge als `DATABASE_URL` in die Secrets eintragen – lokal in
   `.streamlit/secrets.toml` (Vorlage: `.streamlit/secrets.toml.example`),
   in der Cloud unter **Manage app → Settings → Secrets**.
4. App neu starten. In der Seitenleiste erscheint **"☁️ Geteilte
   Cloud-Datenbank aktiv"**, sobald die Verbindung funktioniert.

Ohne `DATABASE_URL` läuft die App weiterhin mit der lokalen SQLite-Datei
(Seitenleiste zeigt dann **"💾 Lokale Datenbank"**) – praktisch zum Testen,
aber nicht für den geteilten Betrieb beider Parteien gedacht.

### 📱 App auf dem Handy nutzen

Es gibt zwei Wege. Beide sind vorbereitet.

#### Variante A – Lokales WLAN (privat, empfohlen für sensible Daten)

Handy und Rechner müssen im selben WLAN sein. Auf dem Rechner:

```bash
./start_mobile.sh
```

Das Skript zeigt eine Adresse wie `http://192.168.1.23:8501` an – diese auf
dem Handy im Browser öffnen. Ohne `DATABASE_URL` laufen die Daten nur über
diesen einen Rechner; mit `DATABASE_URL` (siehe oben) sehen auch von hier
aus beide Parteien dieselbe geteilte Datenbank.

#### Variante B – Streamlit Community Cloud (überall erreichbar, kostenlos)

Feste Web-Adresse, die von jedem Handy aus funktioniert:

1. Auf [share.streamlit.io](https://share.streamlit.io) mit dem GitHub-Konto
   anmelden und **"New app"** wählen.
2. Repository `twhity78/Markanlyse-`, Branch `main`, Hauptdatei
   `streamlit_app.py` auswählen.
3. Unter **Advanced settings → Secrets** Passwort UND `DATABASE_URL`
   hinterlegen (Inhalt aus `.streamlit/secrets.toml.example`):
   ```toml
   app_password = "dein-sicheres-passwort"
   DATABASE_URL = "postgresql://postgres:…@db.….supabase.co:5432/postgres"
   ```
4. **Deploy** klicken. Nach ~1 Minute ist die App unter einer
   `…streamlit.app`-Adresse erreichbar – diese als Lesezeichen aufs Handy legen
   (beide Parteien nutzen dieselbe Adresse).

> **Wichtig bei Variante B:**
> - Der **Passwortschutz** ist bei öffentlichem Hosting dringend empfohlen,
>   da die App Mieter- und Abrechnungsdaten enthält.
> - **`DATABASE_URL` unbedingt mit einrichten** (siehe Abschnitt oben) – ohne
>   sie ist der Speicher der Cloud **flüchtig**: erfasste Ablesungen und
>   Belege gehen bei einem Neustart der App verloren. Die berechneten
>   Abrechnungen bleiben zwar erhalten (sie stammen aus dem Code), aber
>   neu erfasste Daten nicht.

#### Passwortschutz

Der Schutz ist automatisch aktiv, sobald ein Passwort gesetzt ist – über
`.streamlit/secrets.toml` (`app_password = "…"`) oder die Umgebungsvariable
`NK_APP_PASSWORD`. Ohne gesetztes Passwort läuft die App lokal ungeschützt.

#### OCR-Backends (optional)

Die Ablesung funktioniert immer auch manuell. Für die automatische Erkennung
wird das beste verfügbare Backend genutzt:

| Backend | Aktivierung |
|---|---|
| **Claude Vision** | Umgebungsvariable `ANTHROPIC_API_KEY` setzen (empfohlen für Zählerfotos) |
| **Tesseract** | Systempaket `tesseract-ocr` + `pip install pytesseract` |

Ist keines vorhanden, wird der Wert manuell eingegeben – das Foto dient
dann als Nachweis.

Erzeugte PDF-Dateien in `output/` (werden bei Bedarf aus der App heraus neu
erzeugt, sind reine Exporte – die eigentlichen Daten liegen in der Datenbank):

- `NK_Felix_Adameck.pdf` – Nebenkostenabrechnung P1
- `NK_Beltz_Abschluss.pdf` – Abschlussabrechnung P2 (inkl. 80 € Renovierung)
- `NK_Leerstand_Thomas.pdf` – Leerstandskosten
- `NK_Eigentuemer_Zwischenstand.pdf` – Eigentümer-interne Verrechnung
- `NK_Verbrauchsuebersicht.pdf` – Zählerstände + COP-Plausibilität

## Projektstruktur

```
nk_abrechnung/
  config.py      Stammdaten, Zählerstände, Kostenparameter (einzige Datenquelle)
  engine.py      Berechnungslogik (Heizschlüssel, COP, Perioden-Abrechnung)
  db_backend.py  Backend-Umschaltung SQLite ↔ Postgres/Supabase
  database.py    Schema, Seeding, Ablese- und Beleg-Zugriffsfunktionen
  media.py       Bildkompression für Foto-Uploads
  ocr.py         Zählerstand- und Rechnungsbetrag-OCR (Claude Vision / Tesseract)
  pdf.py         PDF-Erzeugung (ReportLab)
main.py          Kommandozeilen-Einstieg
streamlit_app.py Web-Oberfläche: Foto-Ablesung, Belege, Abrechnung
start_mobile.sh  Startet die App im lokalen WLAN
tests/           Regressionstests (SQLite immer, Postgres wenn erreichbar)
```

Lokal ohne `DATABASE_URL` erzeugte Datei (nicht versioniert):
`output/nk_teinacher.db` (SQLite, inkl. Fotos/Belege als Blob). Mit
`DATABASE_URL` liegen alle Daten – auch Fotos und Belege – in der
Postgres-Datenbank, nicht lokal.

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

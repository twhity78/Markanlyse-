# Projektkontext: NK-Abrechnung Teinacher Str. 4, 75387 Neubulach

Sprache: Antworten und Dokumente immer auf Deutsch.
Entwicklungsbranch: `claude/nk-abrechnung-teinacher-46s46g` (nicht auf main pushen, keine PRs ohne Auftrag).

## Stand
- Python-App (Streamlit) in `streamlit_app.py`, Logik in `nk_abrechnung/` (config, engine, database, db_backend, ocr, media, pdf, handbuch).
- Datenbank: SQLite lokal, Postgres/Supabase über `DATABASE_URL` (geteilt, Fotos/Belege als Blob).
- Tests: `python3 -m pytest` (16 Tests, Postgres-Test nur mit lokaler Instanz).
- Excel-Alternative: `NK_Abrechnung_Excel.xlsx` (Formeln, gleiche Ergebnisse wie die App).
- Übergabe-Handbuch: `python3 main.py handbuch` -> `output/Handbuch_Uebergabe.pdf`.

## Fachliche Regeln
- Historische Abrechnungen (Felix, Leerstand, Beltz bis 19.06.2026) bleiben Thomas Weis zugeordnet und unverändert.
- März-2026-WMZ-Stände nie verwenden (falsches Register).
- Neuer Eigentümer wohnt selbst im Haus; Name steht aus: `NEUER_EIGENTUEMER_NAME` in `config.py` einmal eintragen. Zweite Partei: Christine Weis.
- Hauptwasseranschluss geteilt: über Christine laufen nur noch Heizung und Warmwasser. Neue Berechnung ohne Kaltwasser gilt erst ab 01.08.2026 (Excel: Blatt Abr_Folgeperiode). Die App kennt die Folgeperiode noch nicht.

## Offene Punkte
- Ab welchem Monat zahlt Thomas 240 statt 195 EUR/Monat?
- Finale EnBW-Jahresrechnung 2025/26 (Grundpreis prüfen).
- Annahme bestätigen lassen: Warmwasser-m³ werden weiter mit Wasser-/Abwassertarif belastet.
- Folgeperiode in der App abbilden (bisher nur Excel).
- Cloud-Deployment: Code liegt nur auf dem Feature-Branch; Zusammenführen auf main nur auf Wunsch.

## Umgebung
- Python 3.11: `python3 -m pip install -r requirements.txt` (nicht bloßes `pip`, das zeigt auf 3.13).

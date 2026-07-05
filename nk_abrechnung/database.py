"""SQLite-Datenbank für Zähler, Ablesungen, Mieter, Kosten und Zahlungen.

Das Schema folgt dem Vorschlag aus der Projekt-Dokumentation (Abschnitt 10).
Die Datenbank dient als persistenter Speicher inkl. Fotonachweis; die
eigentliche Abrechnung rechnet aus :mod:`nk_abrechnung.config` /
:mod:`nk_abrechnung.engine`. Mit :func:`seed` werden die bekannten
Stammdaten in eine frische Datenbank geschrieben.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from . import config as cfg

SCHEMA = """
CREATE TABLE IF NOT EXISTS meters (
    id          INTEGER PRIMARY KEY,
    serial_no   TEXT NOT NULL UNIQUE,
    type        TEXT NOT NULL,           -- WP | UV | WMZ | KW | WW
    location    TEXT NOT NULL,           -- UG | EG | HAUS
    unit        TEXT NOT NULL,           -- kWh | MWh | m3
    description TEXT
);

CREATE TABLE IF NOT EXISTS meter_readings (
    id         INTEGER PRIMARY KEY,
    meter_id   INTEGER NOT NULL REFERENCES meters(id),
    date       TEXT NOT NULL,            -- ISO-Datum
    value      REAL NOT NULL,
    photo_path TEXT,
    UNIQUE(meter_id, date)
);

CREATE TABLE IF NOT EXISTS tenants (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    start_date      TEXT NOT NULL,
    end_date        TEXT,
    monthly_advance REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS costs (
    id         INTEGER PRIMARY KEY,
    type       TEXT NOT NULL,
    amount     REAL NOT NULL,
    unit       TEXT,
    valid_from TEXT,
    valid_to   TEXT
);

CREATE TABLE IF NOT EXISTS payments (
    id      INTEGER PRIMARY KEY,
    payer   TEXT NOT NULL,
    payee   TEXT NOT NULL,
    date    TEXT,
    amount  REAL NOT NULL,
    note    TEXT
);

CREATE TABLE IF NOT EXISTS receipts (
    id           INTEGER PRIMARY KEY,
    category     TEXT NOT NULL,          -- strom | wasser | versicherung | grundsteuer | niederschlag | sonstiges
    supplier     TEXT,                   -- z.B. EnBW, Wasserversorger, Versicherer
    amount       REAL,                   -- Rechnungsbetrag in EUR
    invoice_date TEXT,                   -- Rechnungsdatum
    period_from  TEXT,                   -- abgerechneter Zeitraum von
    period_to    TEXT,                   -- abgerechneter Zeitraum bis
    file_path    TEXT NOT NULL,          -- Foto-/PDF-Nachweis
    note         TEXT,
    created_at   TEXT DEFAULT (datetime('now'))
);
"""

# Kategorien für Belegnachweise (Eingangsrechnungen).
RECEIPT_CATEGORIES = [
    "strom", "wasser", "versicherung", "grundsteuer", "niederschlag", "sonstiges",
]


def connect(db_path: str | Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_schema(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA)
    con.commit()


def seed(con: sqlite3.Connection) -> None:
    """Befüllt eine frische Datenbank mit den bekannten Stammdaten."""
    cur = con.cursor()

    # Zähler + Ablesungen
    for m in cfg.METERS.values():
        cur.execute(
            "INSERT OR IGNORE INTO meters(serial_no, type, location, unit, description)"
            " VALUES (?,?,?,?,?)",
            (m.serial_no, m.art, m.ort, m.einheit, m.beschreibung),
        )
        meter_id = cur.execute(
            "SELECT id FROM meters WHERE serial_no = ?", (m.serial_no,)
        ).fetchone()[0]
        for tag, wert in sorted(m.staende.items()):
            cur.execute(
                "INSERT OR IGNORE INTO meter_readings(meter_id, date, value)"
                " VALUES (?,?,?)",
                (meter_id, tag.isoformat(), wert),
            )

    # Mieter / Perioden
    for p in (cfg.P1, cfg.P2):
        cur.execute(
            "INSERT INTO tenants(name, start_date, end_date, monthly_advance)"
            " VALUES (?,?,?,?)",
            (p.mieter, p.start.isoformat(), p.ende.isoformat(), p.vorauszahlung_monat),
        )

    # Kostensätze
    kosten = [
        ("strompreis", cfg.STROMPREIS_EUR_KWH, "EUR/kWh", "2024-02-01", None),
        ("enbw_grundpreis_p1", cfg.ENBW_GRUNDPREIS_P1_EUR, "EUR", "2024-02-01", "2025-04-30"),
        ("enbw_grundpreis_monat", cfg.ENBW_GRUNDPREIS_EUR_MONAT, "EUR/Monat", "2025-05-01", None),
        ("gebaeudeversicherung", cfg.GEBAEUDEVERSICHERUNG_EUR_MONAT, "EUR/Monat", None, None),
        ("grundsteuer_b", cfg.GRUNDSTEUER_B_EUR_JAHR, "EUR/Jahr", None, None),
        ("ww_energie", cfg.WW_ENERGIE_EUR_M3, "EUR/m3", None, None),
    ]
    for jahr, tarif in cfg.WASSERTARIF_EUR_M3.items():
        kosten.append(("wassertarif", tarif, "EUR/m3", f"{jahr}-01-01", f"{jahr}-12-31"))
    for jahr, geb in cfg.NS_GEBUEHR_EUR_M2.items():
        kosten.append(("niederschlag", geb, "EUR/m2", f"{jahr}-01-01", f"{jahr}-12-31"))
    cur.executemany(
        "INSERT INTO costs(type, amount, unit, valid_from, valid_to) VALUES (?,?,?,?,?)",
        kosten,
    )

    # Zahlungen Thomas -> Christine
    for betrag in cfg.THOMAS_SONDERZAHLUNGEN_EUR:
        cur.execute(
            "INSERT INTO payments(payer, payee, date, amount, note) VALUES (?,?,?,?,?)",
            ("Thomas Weis", "Christine Weis", None, betrag, "Sonderzahlung"),
        )
    cur.execute(
        "INSERT INTO payments(payer, payee, date, amount, note) VALUES (?,?,?,?,?)",
        ("Thomas Weis", "Christine Weis", "2026-03-01", cfg.THOMAS_SALDO_ALT_EUR,
         "Saldo aus früherer Abrechnung"),
    )

    con.commit()


# ---------------------------------------------------------------------------
# Zugriffsfunktionen (für die Streamlit-App)
# ---------------------------------------------------------------------------


def list_meters(con: sqlite3.Connection) -> list[dict]:
    cur = con.execute(
        "SELECT id, serial_no, type, location, unit, description FROM meters ORDER BY id")
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def add_reading(con: sqlite3.Connection, meter_id: int, datum: str,
                value: float, photo_path: str | None = None) -> None:
    """Fügt eine Ablesung ein oder aktualisiert sie (pro Zähler+Datum eindeutig)."""
    con.execute(
        "INSERT INTO meter_readings(meter_id, date, value, photo_path)"
        " VALUES (?,?,?,?)"
        " ON CONFLICT(meter_id, date) DO UPDATE SET value=excluded.value,"
        " photo_path=COALESCE(excluded.photo_path, meter_readings.photo_path)",
        (meter_id, datum, value, photo_path),
    )
    con.commit()


def list_readings(con: sqlite3.Connection, meter_id: int | None = None) -> list[dict]:
    sql = ("SELECT r.id, m.serial_no, m.description, m.unit, r.date, r.value, "
           "r.photo_path FROM meter_readings r JOIN meters m ON m.id = r.meter_id")
    params: tuple = ()
    if meter_id is not None:
        sql += " WHERE r.meter_id = ?"
        params = (meter_id,)
    sql += " ORDER BY r.date DESC, m.serial_no"
    cur = con.execute(sql, params)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def add_receipt(con: sqlite3.Connection, category: str, file_path: str,
                supplier: str | None = None, amount: float | None = None,
                invoice_date: str | None = None, period_from: str | None = None,
                period_to: str | None = None, note: str | None = None) -> int:
    """Speichert einen Rechnungsbeleg (Foto/PDF-Nachweis) und gibt die ID zurück."""
    cur = con.execute(
        "INSERT INTO receipts(category, supplier, amount, invoice_date,"
        " period_from, period_to, file_path, note) VALUES (?,?,?,?,?,?,?,?)",
        (category, supplier, amount, invoice_date, period_from, period_to,
         file_path, note),
    )
    con.commit()
    return int(cur.lastrowid)


def list_receipts(con: sqlite3.Connection, category: str | None = None) -> list[dict]:
    sql = ("SELECT id, category, supplier, amount, invoice_date, period_from,"
           " period_to, file_path, note FROM receipts")
    params: tuple = ()
    if category:
        sql += " WHERE category = ?"
        params = (category,)
    sql += " ORDER BY invoice_date DESC, id DESC"
    cur = con.execute(sql, params)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def delete_receipt(con: sqlite3.Connection, receipt_id: int) -> str | None:
    """Löscht einen Beleg und gibt den zugehörigen Dateipfad zurück."""
    row = con.execute("SELECT file_path FROM receipts WHERE id = ?",
                      (receipt_id,)).fetchone()
    con.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))
    con.commit()
    return row[0] if row else None


def build(db_path: str | Path, overwrite: bool = False) -> Path:
    """Erzeugt eine einsatzbereite Datenbank und gibt den Pfad zurück."""
    path = Path(db_path)
    if path.exists() and overwrite:
        path.unlink()
    con = connect(path)
    try:
        init_schema(con)
        # nur seeden, wenn noch keine Zähler vorhanden sind
        if con.execute("SELECT COUNT(*) FROM meters").fetchone()[0] == 0:
            seed(con)
    finally:
        con.close()
    return path

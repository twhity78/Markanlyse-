"""Datenbank für Zähler, Ablesungen, Mieter, Kosten, Zahlungen und Belege.

Läuft wahlweise auf SQLite (lokale Datei) oder Postgres/Supabase (geteilter
Cloud-Speicher) – siehe :mod:`nk_abrechnung.db_backend`. Fotos werden direkt
in der Datenbank gespeichert (nicht als Dateipfad), damit beide Parteien sie
jederzeit sehen können, unabhängig davon, von welchem Gerät oder Ort aus sie
erfasst wurden, und auch nach einem Neustart der App in der Cloud.

Das Schema geht auf den Vorschlag aus der Projekt-Dokumentation zurück
(Abschnitt 10), erweitert um Beleg- und Fotoverwaltung. Mit :func:`seed`
werden die bekannten Stammdaten in eine frische Datenbank geschrieben.
"""

from __future__ import annotations

from pathlib import Path

from . import config as cfg
from . import db_backend
from .db_backend import Connection

SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS meters (
    id          INTEGER PRIMARY KEY,
    serial_no   TEXT NOT NULL UNIQUE,
    type        TEXT NOT NULL,           -- WP | UV | WMZ | KW | WW
    location    TEXT NOT NULL,           -- UG | EG | HAUS
    unit        TEXT NOT NULL,           -- kWh | MWh | m3
    description TEXT
);

CREATE TABLE IF NOT EXISTS meter_readings (
    id            INTEGER PRIMARY KEY,
    meter_id      INTEGER NOT NULL REFERENCES meters(id),
    date          TEXT NOT NULL,            -- ISO-Datum
    value         REAL NOT NULL,
    recorded_by   TEXT,                     -- wer hat abgelesen
    photo_filename TEXT,
    photo_mime    TEXT,
    photo_data    BLOB,
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
    recorded_by  TEXT,                   -- wer hat den Beleg erfasst
    file_name    TEXT NOT NULL,
    file_mime    TEXT,
    file_data    BLOB NOT NULL,
    note         TEXT,
    created_at   TEXT DEFAULT (datetime('now'))
);
"""

SCHEMA_POSTGRES = """
CREATE TABLE IF NOT EXISTS meters (
    id          SERIAL PRIMARY KEY,
    serial_no   TEXT NOT NULL UNIQUE,
    type        TEXT NOT NULL,
    location    TEXT NOT NULL,
    unit        TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS meter_readings (
    id             SERIAL PRIMARY KEY,
    meter_id       INTEGER NOT NULL REFERENCES meters(id),
    date           TEXT NOT NULL,
    value          DOUBLE PRECISION NOT NULL,
    recorded_by    TEXT,
    photo_filename TEXT,
    photo_mime     TEXT,
    photo_data     BYTEA,
    UNIQUE(meter_id, date)
);

CREATE TABLE IF NOT EXISTS tenants (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    start_date      TEXT NOT NULL,
    end_date        TEXT,
    monthly_advance DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS costs (
    id         SERIAL PRIMARY KEY,
    type       TEXT NOT NULL,
    amount     DOUBLE PRECISION NOT NULL,
    unit       TEXT,
    valid_from TEXT,
    valid_to   TEXT
);

CREATE TABLE IF NOT EXISTS payments (
    id      SERIAL PRIMARY KEY,
    payer   TEXT NOT NULL,
    payee   TEXT NOT NULL,
    date    TEXT,
    amount  DOUBLE PRECISION NOT NULL,
    note    TEXT
);

CREATE TABLE IF NOT EXISTS receipts (
    id           SERIAL PRIMARY KEY,
    category     TEXT NOT NULL,
    supplier     TEXT,
    amount       DOUBLE PRECISION,
    invoice_date TEXT,
    period_from  TEXT,
    period_to    TEXT,
    recorded_by  TEXT,
    file_name    TEXT NOT NULL,
    file_mime    TEXT,
    file_data    BYTEA NOT NULL,
    note         TEXT,
    created_at   TEXT DEFAULT (now()::text)
);
"""

# Kategorien für Belegnachweise (Eingangsrechnungen).
RECEIPT_CATEGORIES = [
    "strom", "wasser", "versicherung", "grundsteuer", "niederschlag", "sonstiges",
]

# Namen, die in "Erfasst von" zur Auswahl stehen (beide Parteien + Sonstige).
ERFASSER_OPTIONEN = [cfg.NEUER_EIGENTUEMER_NAME, cfg.ZWEITE_PARTEI_NAME, "Sonstige/r"]


def connect(db_path: str | Path) -> Connection:
    return db_backend.connect(db_path)


def init_schema(con: Connection) -> None:
    schema = SCHEMA_POSTGRES if con.backend == "postgres" else SCHEMA_SQLITE
    con.executescript(schema)
    con.commit()


def _blob_param(con: Connection, data: bytes | None):
    if data is None or con.backend != "postgres":
        return data
    import psycopg2
    return psycopg2.Binary(data)


def _to_bytes(value) -> bytes | None:
    if value is None:
        return None
    return bytes(value)


def seed(con: Connection) -> None:
    """Befüllt eine frische Datenbank mit den bekannten Stammdaten."""
    for m in cfg.METERS.values():
        con.execute(
            "INSERT INTO meters(serial_no, type, location, unit, description)"
            " VALUES (?,?,?,?,?) ON CONFLICT (serial_no) DO NOTHING",
            (m.serial_no, m.art, m.ort, m.einheit, m.beschreibung),
        )
        meter_id = con.execute(
            "SELECT id FROM meters WHERE serial_no = ?", (m.serial_no,)
        ).fetchone()[0]
        for tag, wert in sorted(m.staende.items()):
            con.execute(
                "INSERT INTO meter_readings(meter_id, date, value)"
                " VALUES (?,?,?) ON CONFLICT (meter_id, date) DO NOTHING",
                (meter_id, tag.isoformat(), wert),
            )

    for p in (cfg.P1, cfg.P2):
        con.execute(
            "INSERT INTO tenants(name, start_date, end_date, monthly_advance)"
            " VALUES (?,?,?,?)",
            (p.mieter, p.start.isoformat(), p.ende.isoformat(), p.vorauszahlung_monat),
        )

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
    con.executemany(
        "INSERT INTO costs(type, amount, unit, valid_from, valid_to) VALUES (?,?,?,?,?)",
        kosten,
    )

    # Zahlungen Thomas -> Christine (historisch, vor dem Eigentümerwechsel).
    for betrag in cfg.THOMAS_SONDERZAHLUNGEN_EUR:
        con.execute(
            "INSERT INTO payments(payer, payee, date, amount, note) VALUES (?,?,?,?,?)",
            ("Thomas Weis", "Christine Weis", None, betrag, "Sonderzahlung"),
        )
    con.execute(
        "INSERT INTO payments(payer, payee, date, amount, note) VALUES (?,?,?,?,?)",
        ("Thomas Weis", "Christine Weis", "2026-03-01", cfg.THOMAS_SALDO_ALT_EUR,
         "Saldo aus früherer Abrechnung"),
    )

    con.commit()


# ---------------------------------------------------------------------------
# Zugriffsfunktionen (für die Streamlit-App)
# ---------------------------------------------------------------------------


def list_meters(con: Connection) -> list[dict]:
    cur = con.execute(
        "SELECT id, serial_no, type, location, unit, description FROM meters ORDER BY id")
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def add_reading(con: Connection, meter_id: int, datum: str, value: float,
                recorded_by: str | None = None, photo_filename: str | None = None,
                photo_mime: str | None = None, photo_data: bytes | None = None) -> None:
    """Fügt eine Ablesung ein oder aktualisiert sie (pro Zähler+Datum eindeutig).

    Ein vorhandenes Foto bleibt erhalten, wenn keine neuen Fotodaten
    übergeben werden (z.B. beim nachträglichen Korrigieren des Werts).
    """
    con.execute(
        "INSERT INTO meter_readings(meter_id, date, value, recorded_by,"
        " photo_filename, photo_mime, photo_data) VALUES (?,?,?,?,?,?,?)"
        " ON CONFLICT(meter_id, date) DO UPDATE SET"
        " value=excluded.value,"
        " recorded_by=COALESCE(excluded.recorded_by, meter_readings.recorded_by),"
        " photo_filename=COALESCE(excluded.photo_filename, meter_readings.photo_filename),"
        " photo_mime=COALESCE(excluded.photo_mime, meter_readings.photo_mime),"
        " photo_data=COALESCE(excluded.photo_data, meter_readings.photo_data)",
        (meter_id, datum, value, recorded_by, photo_filename, photo_mime,
         _blob_param(con, photo_data)),
    )
    con.commit()


def list_readings(con: Connection, meter_id: int | None = None) -> list[dict]:
    """Ablesungen OHNE Fotodaten (für Tabellen/Übersichten – schnell, kein Blob)."""
    sql = ("SELECT r.id, m.serial_no, m.description, m.unit, r.date, r.value,"
           " r.recorded_by, r.photo_filename,"
           " CASE WHEN r.photo_data IS NULL THEN 0 ELSE 1 END AS has_photo"
           " FROM meter_readings r JOIN meters m ON m.id = r.meter_id")
    params: tuple = ()
    if meter_id is not None:
        sql += " WHERE r.meter_id = ?"
        params = (meter_id,)
    sql += " ORDER BY r.date DESC, m.serial_no"
    cur = con.execute(sql, params)
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    for r in rows:
        r["has_photo"] = bool(r["has_photo"])
    return rows


def get_reading_photo(con: Connection, reading_id: int) -> tuple[bytes, str, str] | None:
    """Lädt das Foto einer Ablesung bei Bedarf nach (Dateiname, MIME, Bytes)."""
    row = con.execute(
        "SELECT photo_filename, photo_mime, photo_data FROM meter_readings WHERE id = ?",
        (reading_id,),
    ).fetchone()
    if not row or row[2] is None:
        return None
    return row[0], row[1], _to_bytes(row[2])


def add_receipt(con: Connection, category: str, file_name: str, file_data: bytes,
                file_mime: str | None = None, supplier: str | None = None,
                amount: float | None = None, invoice_date: str | None = None,
                period_from: str | None = None, period_to: str | None = None,
                recorded_by: str | None = None, note: str | None = None) -> int:
    """Speichert einen Rechnungsbeleg (Foto-/PDF-Nachweis) und gibt die ID zurück."""
    sql = ("INSERT INTO receipts(category, supplier, amount, invoice_date,"
           " period_from, period_to, recorded_by, file_name, file_mime, file_data, note)"
           " VALUES (?,?,?,?,?,?,?,?,?,?,?)")
    params = (category, supplier, amount, invoice_date, period_from, period_to,
              recorded_by, file_name, file_mime, _blob_param(con, file_data), note)
    if con.backend == "postgres":
        cur = con.execute(sql + " RETURNING id", params)
        rid = cur.fetchone()[0]
    else:
        cur = con.execute(sql, params)
        rid = cur.lastrowid
    con.commit()
    return int(rid)


def list_receipts(con: Connection, category: str | None = None) -> list[dict]:
    """Belege OHNE Dateidaten (für Übersichten – schnell, kein Blob)."""
    sql = ("SELECT id, category, supplier, amount, invoice_date, period_from,"
           " period_to, recorded_by, file_name, file_mime, note FROM receipts")
    params: tuple = ()
    if category:
        sql += " WHERE category = ?"
        params = (category,)
    sql += " ORDER BY invoice_date DESC, id DESC"
    cur = con.execute(sql, params)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_receipt_file(con: Connection, receipt_id: int) -> tuple[bytes, str, str] | None:
    """Lädt die Beleg-Datei bei Bedarf nach (Dateiname, MIME, Bytes)."""
    row = con.execute(
        "SELECT file_name, file_mime, file_data FROM receipts WHERE id = ?",
        (receipt_id,),
    ).fetchone()
    if not row:
        return None
    return row[0], row[1], _to_bytes(row[2])


def delete_receipt(con: Connection, receipt_id: int) -> None:
    con.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))
    con.commit()


def build(db_path: str | Path, overwrite: bool = False) -> Path | str:
    """Erzeugt eine einsatzbereite Datenbank.

    Lokal (SQLite) wird bei ``overwrite=True`` die Datei neu angelegt; bei
    Postgres (geteilte Cloud-Datenbank) wird ``overwrite`` ignoriert, um die
    gemeinsamen Daten beider Parteien nicht versehentlich zu löschen.
    """
    url = db_backend.database_url()
    if url:
        con = connect(db_path)
        try:
            init_schema(con)
            if con.execute("SELECT COUNT(*) FROM meters").fetchone()[0] == 0:
                seed(con)
        finally:
            con.close()
        return url

    path = Path(db_path)
    if path.exists() and overwrite:
        path.unlink()
    con = connect(path)
    try:
        init_schema(con)
        if con.execute("SELECT COUNT(*) FROM meters").fetchone()[0] == 0:
            seed(con)
    finally:
        con.close()
    return path

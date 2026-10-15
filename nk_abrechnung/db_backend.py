"""Datenbank-Backend-Abstraktion: SQLite (lokal) oder Postgres/Supabase (Cloud).

Die SQLite-Datei auf Streamlit Community Cloud ist **flüchtig** – bei jedem
Neustart der App gehen erfasste Ablesungen und Belege verloren. Für einen
dauerhaften Cloud-Speicher kann stattdessen eine Postgres-Datenbank (z. B.
ein kostenloses Supabase-Projekt) angebunden werden.

Auswahl automatisch über die Verbindungszeichenfolge:

* ``DATABASE_URL`` in ``st.secrets`` (Streamlit Cloud) oder als
  Umgebungsvariable (lokal) -> Postgres
* nicht gesetzt -> lokale SQLite-Datei (Standard)

Beide Backends werden über dieselbe, sqlite3-ähnliche Schnittstelle
angesprochen (``execute``/``executemany``/``commit``/``close``, Platzhalter
``?``), sodass :mod:`nk_abrechnung.database` backend-unabhängig bleibt.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Iterable


def database_url() -> str | None:
    """Liest ``DATABASE_URL`` aus st.secrets (Cloud) oder der Umgebung (lokal)."""
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return str(st.secrets["DATABASE_URL"])
    except Exception:
        pass
    return os.environ.get("DATABASE_URL")


def backend_name() -> str:
    return "postgres" if database_url() else "sqlite"


class Cursor:
    """Einheitlicher Cursor für SQLite und Postgres."""

    def __init__(self, raw: Any, backend: str):
        self._raw = raw
        self.backend = backend

    @property
    def description(self):
        return self._raw.description

    @property
    def lastrowid(self):
        return getattr(self._raw, "lastrowid", None)

    def fetchone(self):
        return self._raw.fetchone()

    def fetchall(self):
        return self._raw.fetchall()


class Connection:
    """Gemeinsame Schnittstelle über SQLite- und Postgres-Verbindungen.

    Nutzt durchgängig ``?`` als Platzhalter (wie sqlite3); für Postgres wird
    automatisch auf ``%s`` übersetzt.
    """

    def __init__(self, raw: Any, backend: str):
        self._raw = raw
        self.backend = backend

    def _adapt(self, sql: str) -> str:
        return sql.replace("?", "%s") if self.backend == "postgres" else sql

    def execute(self, sql: str, params: tuple = ()) -> Cursor:
        cur = self._raw.cursor()
        cur.execute(self._adapt(sql), params)
        return Cursor(cur, self.backend)

    def executemany(self, sql: str, seq_of_params: Iterable[tuple]) -> None:
        cur = self._raw.cursor()
        cur.executemany(self._adapt(sql), list(seq_of_params))

    def executescript(self, sql: str) -> None:
        """Führt mehrere ';'-getrennte Anweisungen aus (nur Schema-DDL)."""
        if self.backend == "postgres":
            cur = self._raw.cursor()
            cur.execute(sql)
        else:
            self._raw.executescript(sql)

    def commit(self) -> None:
        self._raw.commit()

    def close(self) -> None:
        self._raw.close()


def connect(sqlite_path: str | Path) -> Connection:
    """Verbindet zu Postgres (falls ``DATABASE_URL`` gesetzt) oder SQLite."""
    url = database_url()
    if url:
        import psycopg2
        raw = psycopg2.connect(url)
        return Connection(raw, "postgres")

    raw = sqlite3.connect(str(sqlite_path))
    raw.execute("PRAGMA foreign_keys = ON")
    return Connection(raw, "sqlite")

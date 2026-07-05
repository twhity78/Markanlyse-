"""Regressionstests: die Berechnung muss die dokumentierten Ergebnisse
(Abschnitt 6 der Projekt-Zusammenfassung) reproduzieren.

Toleranz 2 Cent, da das Ausgangsdokument an einzelnen Stellen
uneinheitlich rundet (z. B. Grundsteuer 235,97 statt 235,98).
"""

import sqlite3

import pytest

from nk_abrechnung import config as cfg
from nk_abrechnung import engine as e
from nk_abrechnung import database

TOL = 0.02


def test_heizschluessel():
    pug1 = e.heizschluessel_ug(cfg.STICHTAG_START, cfg.STICHTAG_MITTE)
    pug2 = e.heizschluessel_ug(cfg.STICHTAG_MITTE, cfg.STICHTAG_ENDE)
    assert pug1 == pytest.approx(0.4660, abs=1e-3)
    assert pug2 == pytest.approx(0.6889, abs=1e-3)


def test_cop_plausibilitaet():
    # Gesamtperiode plausibel, März-Teilperioden wurden bewusst verworfen.
    assert e.cop(cfg.STICHTAG_MITTE, cfg.STICHTAG_ENDE) == pytest.approx(2.08, abs=0.01)


def test_felix():
    a = e.abrechnung_p1()
    assert a.soll == pytest.approx(3262.66, abs=TOL)
    assert a.ist_zahlung == pytest.approx(2545.00, abs=TOL)
    assert a.saldo == pytest.approx(717.66, abs=TOL)


def test_leerstand():
    a = e.abrechnung_leerstand()
    assert a.soll == pytest.approx(706.81, abs=TOL)


def test_beltz():
    a = e.abrechnung_p2()
    assert a.nk_netto == pytest.approx(3030.31, abs=TOL)
    assert a.soll == pytest.approx(3110.31, abs=TOL)
    assert a.ist_zahlung == pytest.approx(2585.00, abs=TOL)
    assert a.saldo == pytest.approx(525.31, abs=TOL)


@pytest.mark.parametrize("position,erwartet", [
    ("Heizkosten Wärmepumpe", 1519.83),
    ("Warmwasser-Heizenergie", 53.64),
    ("Haushaltsstrom UV", 409.86),
    ("Stromgrundpreis (UG-Anteil)", 168.24),
    ("Wasser/Abwasser", 385.04),
])
def test_beltz_positionen(position, erwartet):
    a = e.abrechnung_p2()
    werte = dict(a.positionen)
    assert werte[position] == pytest.approx(erwartet, abs=TOL)


def test_ww_eg_kulanz():
    k = e.ww_eg_kulanz()
    assert k["m3"] == pytest.approx(113.547, abs=1e-3)
    assert k["wert_eur"] == pytest.approx(584.27, abs=TOL)


def test_monatsverteilung():
    # P1 startet 02/2024 über 15 Monate -> 11 in 2024, 4 in 2025.
    v = e.monate_pro_jahr(cfg.P1.start, cfg.P1.monate)
    assert v == {2024: 11, 2025: 4}


def test_belege(tmp_path):
    path = database.build(tmp_path / "test.db", overwrite=True)
    con = database.connect(path)
    try:
        rid = database.add_receipt(
            con, "strom", "/x/enbw.pdf", supplier="EnBW", amount=1234.56,
            invoice_date="2026-03-01", period_from="2025-05-01",
            period_to="2026-04-30", note="Jahresrechnung")
        database.add_receipt(con, "versicherung", "/x/v.jpg", amount=290.16)
        assert len(database.list_receipts(con)) == 2
        assert len(database.list_receipts(con, "strom")) == 1
        assert database.list_receipts(con, "strom")[0]["amount"] == 1234.56
        pfad = database.delete_receipt(con, rid)
        assert pfad == "/x/enbw.pdf"
        assert len(database.list_receipts(con)) == 1
    finally:
        con.close()


def test_datenbank_seed(tmp_path):
    path = database.build(tmp_path / "test.db", overwrite=True)
    con = sqlite3.connect(path)
    try:
        anz_meter = con.execute("SELECT COUNT(*) FROM meters").fetchone()[0]
        anz_reading = con.execute("SELECT COUNT(*) FROM meter_readings").fetchone()[0]
    finally:
        con.close()
    assert anz_meter == len(cfg.METERS)
    assert anz_reading >= 20

"""Stammdaten, Zählerstände und Kostenparameter.

Alle Werte stammen aus der Projekt-Zusammenfassung (Stand 19.06.2026).
Änderungen an Zählerständen oder Tarifen werden ausschließlich hier
gepflegt – die Berechnungslogik in :mod:`nk_abrechnung.engine` bleibt
davon unberührt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


# ---------------------------------------------------------------------------
# Objekt & Eigentümer
# ---------------------------------------------------------------------------

OBJEKT = {
    "adresse": "Teinacher Str. 4, 75387 Neubulach",
    "eigentuemer": ["Thomas Weis (50%)", "Christine Weis (50%)"],
    "flaeche_ug_m2": 88.0,
    "flaeche_eg_m2": 182.0,
    "flaeche_gesamt_m2": 270.0,
}

# UG-Anteil an der Gesamtfläche = 88 / 270 = 32,59 %
UG_ANTEIL = OBJEKT["flaeche_ug_m2"] / OBJEKT["flaeche_gesamt_m2"]


# ---------------------------------------------------------------------------
# Kostenparameter
# ---------------------------------------------------------------------------

# Strom (EnBW)
STROMPREIS_EUR_KWH = 0.2462

# EnBW-Grundpreis: Periode 1 hat einen eigenen Rechnungsbetrag (563,11 €
# für 15 Monate). Periode 2 ergibt den Monatssatz, der auch für Leerstand
# und Beltz-Periode angesetzt wird.
ENBW_GRUNDPREIS_P1_EUR = 563.11
ENBW_GRUNDPREIS_P2_EUR = 375.41
ENBW_GRUNDPREIS_MONATE_P2 = 8
ENBW_GRUNDPREIS_EUR_MONAT = ENBW_GRUNDPREIS_P2_EUR / ENBW_GRUNDPREIS_MONATE_P2  # 46,93 €

# Wasser (inkl. Abwasser), Tarif pro Kalenderjahr
WASSERTARIF_EUR_M3 = {
    2024: 7.63,
    2025: 7.44,
    2026: 7.44,  # Fortschreibung 2025er-Tarif bis neue Gebührensatzung vorliegt
}

# Warmwasser-Heizenergie (Mitsubishi-Gerätekennwert)
WW_KWH_PRO_M3 = 20.9
WW_ENERGIE_EUR_M3 = WW_KWH_PRO_M3 * STROMPREIS_EUR_KWH  # 5,14558 €/m³

# Fixkosten UG
GEBAEUDEVERSICHERUNG_EUR_MONAT = 24.18
GRUNDSTEUER_B_EUR_JAHR = 188.78
GRUNDSTEUER_EUR_MONAT = GRUNDSTEUER_B_EUR_JAHR / 12  # 15,73 €

# Niederschlagswasser: 226 m² versiegelte Fläche, Gebühr pro Kalenderjahr,
# UG-Anteil 32,59 %, auf den Monat umgelegt.
NS_FLAECHE_M2 = 226.0
NS_GEBUEHR_EUR_M2 = {
    2024: 0.99,
    2025: 0.81,
    2026: 0.81,  # Fortschreibung, bis neue Gebühr vorliegt
}


def niederschlag_eur_monat(jahr: int) -> float:
    """Monatlicher UG-Anteil der Niederschlagswassergebühr für ``jahr``.

    Kaufmännisch auf Cent gerundet (der Monatssatz ist der abgerechnete
    Grundwert, vgl. Dokumentation: 6,08 € für 2024 / 4,97 € für 2025).
    """
    gebuehr = NS_GEBUEHR_EUR_M2.get(jahr, NS_GEBUEHR_EUR_M2[2025])
    return round(NS_FLAECHE_M2 * gebuehr / 12 * UG_ANTEIL, 2)


# ---------------------------------------------------------------------------
# Zähler
# ---------------------------------------------------------------------------

# Ablese-Stichtage. "Mai 2025" ist die Grenze P1 -> Leerstand,
# "Jun 2026" ist der Abrechnungsstichtag.
STICHTAG_START = date(2024, 2, 1)
STICHTAG_MITTE = date(2025, 5, 1)
STICHTAG_ENDE = date(2026, 6, 19)


@dataclass(frozen=True)
class Meter:
    """Ein physischer Zähler mit seinen Stichtags-Ständen."""

    key: str
    serial_no: str
    art: str            # WP | UV | WMZ | KW | WW
    ort: str            # UG | EG | HAUS
    einheit: str        # kWh | MWh | m3
    beschreibung: str
    staende: dict[date, float] = field(default_factory=dict)

    def delta(self, von: date, bis: date) -> float:
        """Verbrauch zwischen zwei Stichtagen in Zähler-Einheit."""
        return self.staende[bis] - self.staende[von]


# März-2026-Stände sind bewusst NICHT hinterlegt: WMZ-Register war falsch
# (COP-Prüfung fehlgeschlagen), Strom-März-Stände für die Abrechnung nicht
# benötigt. Es wird ausschließlich mit den drei belastbaren Stichtagen
# gerechnet.
METERS: dict[str, Meter] = {
    "WP": Meter(
        key="WP", serial_no="401746-0222", art="WP", ort="HAUS", einheit="kWh",
        beschreibung="WP-Strom (Wärmepumpe)",
        staende={STICHTAG_START: 17705.44, STICHTAG_MITTE: 29062.26, STICHTAG_ENDE: 40467.30},
    ),
    "UV": Meter(
        key="UV", serial_no="401349-0222", art="UV", ort="UG", einheit="kWh",
        beschreibung="Haushaltsstrom UG (UV)",
        staende={STICHTAG_START: 3396.16, STICHTAG_MITTE: 5480.90, STICHTAG_ENDE: 7599.68},
    ),
    "WMZ_UG": Meter(
        key="WMZ_UG", serial_no="12654509", art="WMZ", ort="UG", einheit="MWh",
        beschreibung="Wärmemengenzähler UG",
        staende={STICHTAG_START: 32.500, STICHTAG_MITTE: 49.950, STICHTAG_ENDE: 66.322},
    ),
    "WMZ_EG": Meter(
        key="WMZ_EG", serial_no="12654523", art="WMZ", ort="EG", einheit="MWh",
        beschreibung="Wärmemengenzähler EG+DG",
        staende={STICHTAG_START: 33.000, STICHTAG_MITTE: 53.000, STICHTAG_ENDE: 60.394},
    ),
    "KW_UG": Meter(
        key="KW_UG", serial_no="12050176", art="KW", ort="UG", einheit="m3",
        beschreibung="Kaltwasser UG",
        staende={STICHTAG_START: 61.904, STICHTAG_MITTE: 107.810, STICHTAG_ENDE: 149.138},
    ),
    "WW_UG": Meter(
        key="WW_UG", serial_no="20424827", art="WW", ort="UG", einheit="m3",
        beschreibung="Warmwasser UG",
        staende={STICHTAG_START: 35.021, STICHTAG_MITTE: 53.070, STICHTAG_ENDE: 63.495},
    ),
    "WW_EG": Meter(
        key="WW_EG", serial_no="21415602", art="WW", ort="EG", einheit="m3",
        beschreibung="Warmwasser EG (Kulanz – Christine, erlassen)",
        staende={STICHTAG_START: 6.569, STICHTAG_ENDE: 120.116},
    ),
}


# ---------------------------------------------------------------------------
# Perioden / Mieter
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Periode:
    key: str
    label: str
    mieter: str
    start: date
    ende: date
    monate: int
    vorauszahlung_monat: float      # nominale Vorauszahlung € pro Monat
    ablese_von: date
    ablese_bis: date
    ist_geleistet: float | None = None  # tatsächlich erhaltene Zahlungen (falls != nominal)

    @property
    def ist_zahlung(self) -> float:
        """Tatsächlich geleistete Zahlungen (Fallback: nominal × Monate)."""
        if self.ist_geleistet is not None:
            return self.ist_geleistet
        return self.vorauszahlung_monat * self.monate


# P1 Felix: eigene Zählerperiode Feb 2024 -> Mai 2025 (15 Monate).
P1 = Periode(
    key="P1", label="Periode 1", mieter="Felix Adameck",
    start=date(2024, 2, 1), ende=date(2025, 4, 30), monate=15,
    vorauszahlung_monat=195.0,
    ablese_von=STICHTAG_START, ablese_bis=STICHTAG_MITTE,
    ist_geleistet=2545.00,  # tatsächlich erhaltene Vorauszahlungen (vgl. Doku 6.1)
)

# Leerstand und Beltz teilen sich die Zählerperiode Mai 2025 -> Jun 2026
# (14 Monate gesamt): Leerstand 3/14, Beltz 11/14.
LEERSTAND = Periode(
    key="LEER", label="Leerstand", mieter="Thomas Weis (Eigentümer)",
    start=date(2025, 5, 1), ende=date(2025, 7, 31), monate=3,
    vorauszahlung_monat=0.0,
    ablese_von=STICHTAG_MITTE, ablese_bis=STICHTAG_ENDE,
)

P2 = Periode(
    key="P2", label="Periode 2", mieter="Fam. Kristin & Maximilian Beltz",
    start=date(2025, 8, 1), ende=date(2026, 6, 19), monate=11,
    vorauszahlung_monat=235.0,
    ablese_von=STICHTAG_MITTE, ablese_bis=STICHTAG_ENDE,
)

# Gesamt-Monate der geteilten Zählerperiode Mai25 -> Jun26.
ZAEHLERPERIODE_P2_MONATE = LEERSTAND.monate + P2.monate  # 14


# ---------------------------------------------------------------------------
# Sondervereinbarungen
# ---------------------------------------------------------------------------

# Renovierungspauschale Beltz (vereinbart).
BELTZ_RENOVIERUNG_EUR = 80.0

# Zahlungen Thomas -> Christine (Eigentümer-intern).
THOMAS_SONDERZAHLUNGEN_EUR = [500.0, 273.0, 210.74, 104.0]
THOMAS_SALDO_ALT_EUR = 81.99  # Einmalzahlung März 2026 aus früherer Abrechnung

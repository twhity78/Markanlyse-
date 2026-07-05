"""Berechnungslogik der Nebenkostenabrechnung.

Sämtliche Beträge werden aus den Roh-Zählerständen und den Parametern in
:mod:`nk_abrechnung.config` abgeleitet. Die Methodik entspricht der
Projekt-Dokumentation (Abschnitt 5):

* Heizschlüssel UG (``pug``) je Zählerperiode aus WMZ-Deltas
* Leerstand-/Beltz-Split der geteilten Zählerperiode (3/14 bzw. 11/14)
* Warmwasser-Heizenergie über den Gerätekennwert
* Wasser- und Niederschlagsanteile monatsgenau nach Kalenderjahr-Tarif
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from . import config as cfg


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def monate_pro_jahr(start: date, monate: int) -> dict[int, int]:
    """Verteilt ``monate`` ab ``start`` auf Kalenderjahre.

    Beispiel: Start 02/2024, 15 Monate -> {2024: 11, 2025: 4}.
    """
    verteilung: dict[int, int] = {}
    jahr, monat = start.year, start.month
    for _ in range(monate):
        verteilung[jahr] = verteilung.get(jahr, 0) + 1
        monat += 1
        if monat > 12:
            monat = 1
            jahr += 1
    return verteilung


def wasserkosten(m3: float, start: date, monate: int) -> float:
    """Wasser-/Abwasserkosten für ein Volumen, monatsanteilig nach Tarifjahr."""
    verteilung = monate_pro_jahr(start, monate)
    kosten = 0.0
    for jahr, anzahl in verteilung.items():
        tarif = cfg.WASSERTARIF_EUR_M3.get(jahr, cfg.WASSERTARIF_EUR_M3[2025])
        anteil_m3 = m3 * anzahl / monate
        kosten += anteil_m3 * tarif
    return kosten


def niederschlagskosten(start: date, monate: int) -> float:
    """Niederschlagswasser (UG-Anteil) über ``monate`` ab ``start``."""
    verteilung = monate_pro_jahr(start, monate)
    return sum(cfg.niederschlag_eur_monat(jahr) * anzahl
               for jahr, anzahl in verteilung.items())


# ---------------------------------------------------------------------------
# Heizschlüssel & Plausibilität (COP)
# ---------------------------------------------------------------------------


def heizschluessel_ug(von: date, bis: date) -> float:
    """UG-Anteil an der Heizwärme (``pug``) aus den WMZ-Deltas einer Periode."""
    ug = cfg.METERS["WMZ_UG"].delta(von, bis)
    eg = cfg.METERS["WMZ_EG"].delta(von, bis)
    return ug / (ug + eg)


def cop(von: date, bis: date) -> float:
    """Leistungszahl (COP) = erzeugte Wärme (WMZ gesamt) / WP-Stromeinsatz.

    Dient der Plausibilitätsprüfung der WMZ-Stände.
    """
    waerme_mwh = (cfg.METERS["WMZ_UG"].delta(von, bis)
                  + cfg.METERS["WMZ_EG"].delta(von, bis))
    strom_kwh = cfg.METERS["WP"].delta(von, bis)
    return (waerme_mwh * 1000.0) / strom_kwh


# ---------------------------------------------------------------------------
# Ergebnis-Strukturen
# ---------------------------------------------------------------------------


@dataclass
class Abrechnung:
    """Ergebnis einer Perioden-Abrechnung."""

    titel: str
    mieter: str
    zeitraum: str
    positionen: list[tuple[str, float]] = field(default_factory=list)
    ist_zahlung: float = 0.0
    zusatz: list[tuple[str, float]] = field(default_factory=list)  # z.B. Renovierung

    def add(self, bezeichnung: str, betrag: float) -> None:
        self.positionen.append((bezeichnung, round(betrag, 2)))

    @property
    def nk_netto(self) -> float:
        return round(sum(b for _, b in self.positionen), 2)

    @property
    def soll(self) -> float:
        return round(self.nk_netto + sum(b for _, b in self.zusatz), 2)

    @property
    def saldo(self) -> float:
        """Positiv = Nachzahlung des Mieters, negativ = Guthaben."""
        return round(self.soll - self.ist_zahlung, 2)


# ---------------------------------------------------------------------------
# Perioden-Abrechnungen
# ---------------------------------------------------------------------------


def _stromgrundpreis(monate: int) -> float:
    return cfg.ENBW_GRUNDPREIS_EUR_MONAT * monate * cfg.UG_ANTEIL


def abrechnung_p1() -> Abrechnung:
    """Felix Adameck – eigene Zählerperiode Feb 2024 -> Mai 2025."""
    p = cfg.P1
    von, bis = p.ablese_von, p.ablese_bis
    pug = heizschluessel_ug(von, bis)

    a = Abrechnung("Nebenkostenabrechnung", p.mieter,
                   f"{p.start:%d.%m.%Y} – {p.ende:%d.%m.%Y} ({p.monate} Monate)")

    wp_kwh = cfg.METERS["WP"].delta(von, bis)
    a.add("Heizkosten Wärmepumpe", wp_kwh * pug * cfg.STROMPREIS_EUR_KWH)

    ww_m3 = cfg.METERS["WW_UG"].delta(von, bis)
    a.add("Warmwasser-Heizenergie", ww_m3 * cfg.WW_ENERGIE_EUR_M3)

    uv_kwh = cfg.METERS["UV"].delta(von, bis)
    a.add("Haushaltsstrom UV", uv_kwh * cfg.STROMPREIS_EUR_KWH)

    # P1 hat einen eigenen EnBW-Grundpreis-Rechnungsbetrag (563,11 €).
    a.add("Stromgrundpreis (UG-Anteil)", cfg.ENBW_GRUNDPREIS_P1_EUR * cfg.UG_ANTEIL)

    # Wasser = Kaltwasser + Warmwasser-Volumen, monatsanteilig nach Tarifjahr.
    kw_m3 = cfg.METERS["KW_UG"].delta(von, bis)
    wasser_m3 = kw_m3 + ww_m3
    verteilung = monate_pro_jahr(p.start, p.monate)
    for jahr in sorted(verteilung):
        tarif = cfg.WASSERTARIF_EUR_M3.get(jahr, cfg.WASSERTARIF_EUR_M3[2025])
        anteil = wasser_m3 * verteilung[jahr] / p.monate
        a.add(f"Wasser/Abwasser {jahr}", anteil * tarif)

    a.add("Gebäudeversicherung", cfg.GEBAEUDEVERSICHERUNG_EUR_MONAT * p.monate)
    a.add("Grundsteuer B", cfg.GRUNDSTEUER_EUR_MONAT * p.monate)

    for jahr in sorted(verteilung):
        a.add(f"Niederschlagswasser {jahr}",
              cfg.niederschlag_eur_monat(jahr) * verteilung[jahr])

    a.ist_zahlung = p.ist_zahlung
    return a


def abrechnung_p2() -> Abrechnung:
    """Fam. Beltz – Anteil 11/14 der Zählerperiode Mai 2025 -> Jun 2026."""
    p = cfg.P2
    von, bis = p.ablese_von, p.ablese_bis
    pug = heizschluessel_ug(von, bis)
    anteil = p.monate / cfg.ZAEHLERPERIODE_P2_MONATE  # 11/14

    a = Abrechnung("Abschlussabrechnung", p.mieter,
                   f"{p.start:%d.%m.%Y} – {p.ende:%d.%m.%Y} ({p.monate} Monate)")

    wp_kwh = cfg.METERS["WP"].delta(von, bis) * anteil
    a.add("Heizkosten Wärmepumpe", wp_kwh * pug * cfg.STROMPREIS_EUR_KWH)

    # Warmwasser: während des Leerstands kein Verbrauch -> voller Delta zu Beltz.
    ww_m3 = cfg.METERS["WW_UG"].delta(von, bis)
    a.add("Warmwasser-Heizenergie", ww_m3 * cfg.WW_ENERGIE_EUR_M3)

    uv_kwh = cfg.METERS["UV"].delta(von, bis) * anteil
    a.add("Haushaltsstrom UV", uv_kwh * cfg.STROMPREIS_EUR_KWH)

    a.add("Stromgrundpreis (UG-Anteil)", _stromgrundpreis(p.monate))

    kw_m3 = cfg.METERS["KW_UG"].delta(von, bis)
    wasser_m3 = kw_m3 + ww_m3
    a.add("Wasser/Abwasser", wasserkosten(wasser_m3, p.start, p.monate))

    a.add("Gebäudeversicherung", cfg.GEBAEUDEVERSICHERUNG_EUR_MONAT * p.monate)
    a.add("Grundsteuer B", cfg.GRUNDSTEUER_EUR_MONAT * p.monate)
    a.add("Niederschlagswasser", niederschlagskosten(p.start, p.monate))

    a.zusatz.append(("Renovierung (vereinbart)", cfg.BELTZ_RENOVIERUNG_EUR))
    a.ist_zahlung = p.ist_zahlung
    return a


def abrechnung_leerstand() -> Abrechnung:
    """Leerstand – Anteil 3/14 der Zählerperiode, getragen von Thomas Weis."""
    p = cfg.LEERSTAND
    von, bis = p.ablese_von, p.ablese_bis
    pug = heizschluessel_ug(von, bis)
    anteil = p.monate / cfg.ZAEHLERPERIODE_P2_MONATE  # 3/14

    a = Abrechnung("Leerstandsabrechnung", p.mieter,
                   f"{p.start:%d.%m.%Y} – {p.ende:%d.%m.%Y} ({p.monate} Monate)")

    wp_kwh = cfg.METERS["WP"].delta(von, bis) * anteil
    a.add("WP-Strom fiktiv (Heizung)", wp_kwh * pug * cfg.STROMPREIS_EUR_KWH)

    uv_kwh = cfg.METERS["UV"].delta(von, bis) * anteil
    a.add("Haushaltsstrom UV fiktiv", uv_kwh * cfg.STROMPREIS_EUR_KWH)

    a.add("Stromgrundpreis (UG-Anteil)", _stromgrundpreis(p.monate))
    a.add("Gebäudeversicherung", cfg.GEBAEUDEVERSICHERUNG_EUR_MONAT * p.monate)
    a.add("Grundsteuer B", cfg.GRUNDSTEUER_EUR_MONAT * p.monate)
    a.add("Niederschlagswasser", niederschlagskosten(p.start, p.monate))

    a.ist_zahlung = 0.0
    return a


# ---------------------------------------------------------------------------
# Kulanz Warmwasser EG (Christine)
# ---------------------------------------------------------------------------


def ww_eg_kulanz() -> dict[str, float]:
    """Erlassener Warmwasser-Verbrauch EG (Christine, Eigennutzung)."""
    m = cfg.METERS["WW_EG"]
    m3 = m.delta(cfg.STICHTAG_START, cfg.STICHTAG_ENDE)
    return {"m3": round(m3, 3), "wert_eur": round(m3 * cfg.WW_ENERGIE_EUR_M3, 2)}


def alle_abrechnungen() -> dict[str, Abrechnung]:
    return {
        "P1": abrechnung_p1(),
        "LEER": abrechnung_leerstand(),
        "P2": abrechnung_p2(),
    }


# ---------------------------------------------------------------------------
# Eigentümer-interne Abrechnung Thomas <-> Christine
# ---------------------------------------------------------------------------


@dataclass
class EigentuemerSaldo:
    """Zwischenstand der Eigentümer-internen Verrechnung.

    Thomas trägt den Leerstand und schuldet Christine (Eigennutzerin EG)
    die auf das UG entfallenden Kosten, soweit sie nicht durch die
    Mieter-Vorauszahlungen bzw. seine Zahlungen gedeckt sind.
    ``beltz_vorauszahlung_monat`` ist der noch zu klärende Punkt
    (195 € oder 240 € ab welchem Monat).
    """

    positionen: list[tuple[str, float]]
    sonderzahlungen: float
    saldo_alt: float
    ww_eg_erlassen: float
    offene_punkte: list[str]

    @property
    def summe_positionen(self) -> float:
        return round(sum(b for _, b in self.positionen), 2)

    @property
    def zwischensaldo(self) -> float:
        return round(self.summe_positionen + self.sonderzahlungen + self.saldo_alt, 2)


def eigentuemer_zwischenstand(beltz_vorauszahlung_monat: float = 195.0) -> EigentuemerSaldo:
    """Zwischenstand Thomas -> Christine.

    Positiv = Betrag, den Thomas an Christine leistet (bzw. bereits geleistet
    hat); die Mieter-SOLL/IST-Differenzen fließen als Nachforderung ein.
    """
    p1 = abrechnung_p1()
    leer = abrechnung_leerstand()
    p2 = abrechnung_p2()

    beltz_ist = beltz_vorauszahlung_monat * cfg.P2.monate

    positionen = [
        ("P1 Felix – Vorauszahlungs-Differenz (SOLL−IST)",
         round(p1.soll - cfg.P1.vorauszahlung_monat * cfg.P1.monate, 2)),
        ("Leerstand – von Thomas getragen", round(leer.soll, 2)),
        ("P2 Beltz – Vorauszahlungs-Differenz (SOLL−IST)",
         round(p2.soll - beltz_ist, 2)),
    ]

    kulanz = ww_eg_kulanz()
    return EigentuemerSaldo(
        positionen=positionen,
        sonderzahlungen=round(sum(cfg.THOMAS_SONDERZAHLUNGEN_EUR), 2),
        saldo_alt=cfg.THOMAS_SALDO_ALT_EUR,
        ww_eg_erlassen=kulanz["wert_eur"],
        offene_punkte=[
            "Ab welchem Monat zahlt Thomas 240 €/Mon statt 195 €/Mon?",
            f"Beltz-Vorauszahlung im Zwischenstand angesetzt mit "
            f"{beltz_vorauszahlung_monat:.0f} €/Mon.",
            "Finale EnBW-Jahresrechnung 2025/26 zur Grundpreis-Verifizierung "
            "steht aus.",
        ],
    )

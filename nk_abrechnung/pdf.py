"""PDF-Erzeugung der Abrechnungen mit ReportLab."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

from . import config as cfg
from . import engine as e

# Farben / Stil
PRIMARY = colors.HexColor("#1f3a5f")
LIGHT = colors.HexColor("#eef2f7")
MUTED = colors.HexColor("#555555")


def _eur(v: float) -> str:
    """Formatiert einen Betrag deutsch: 1.234,56 €."""
    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], fontSize=17,
                                textColor=PRIMARY, spaceAfter=2),
        "sub": ParagraphStyle("s", parent=base["Normal"], fontSize=10,
                              textColor=MUTED, spaceAfter=10),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=12,
                             textColor=PRIMARY, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("b", parent=base["Normal"], fontSize=9.5,
                               leading=13),
        "small": ParagraphStyle("sm", parent=base["Normal"], fontSize=8,
                                textColor=MUTED, leading=11),
    }


def _kopf(story, s, titel, mieter, zeitraum):
    story.append(Paragraph(titel, s["title"]))
    story.append(Paragraph(cfg.OBJEKT["adresse"], s["sub"]))
    kopf = Table(
        [[Paragraph(f"<b>Mieter/Partei:</b> {mieter}", s["body"]),
          Paragraph(f"<b>Abrechnungszeitraum:</b><br/>{zeitraum}", s["body"])]],
        colWidths=[95 * mm, 75 * mm],
    )
    kopf.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(kopf)
    story.append(Spacer(1, 8))


def _positions_tabelle(story, s, ab: e.Abrechnung, saldo_label: str):
    rows = [["Position", "Betrag"]]
    for bez, betrag in ab.positionen:
        rows.append([bez, _eur(betrag)])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, len(ab.positionen)), [colors.white, LIGHT]),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]

    r = len(rows)
    rows.append(["Nebenkosten netto", _eur(ab.nk_netto)])
    style += [("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"),
              ("LINEABOVE", (0, r), (-1, r), 0.8, PRIMARY)]

    for bez, betrag in ab.zusatz:
        rows.append([bez, _eur(betrag)])

    r = len(rows)
    rows.append(["Gesamtforderung (SOLL)", _eur(ab.soll)])
    style += [("FONTNAME", (0, r), (-1, r), "Helvetica-Bold")]

    r = len(rows)
    rows.append(["Geleistete Zahlungen (IST)", "− " + _eur(ab.ist_zahlung)])

    r = len(rows)
    vorz = "Nachzahlung" if ab.saldo >= 0 else "Guthaben"
    rows.append([f"{saldo_label} ({vorz})", _eur(abs(ab.saldo))])
    style += [("FONTNAME", (0, r), (-1, r), "Helvetica-Bold"),
              ("FONTSIZE", (0, r), (-1, r), 11),
              ("BACKGROUND", (0, r), (-1, r),
               colors.HexColor("#d9534f") if ab.saldo >= 0 else colors.HexColor("#5cb85c")),
              ("TEXTCOLOR", (0, r), (-1, r), colors.white),
              ("LINEABOVE", (0, r), (-1, r), 0.8, PRIMARY)]

    t = Table(rows, colWidths=[120 * mm, 50 * mm])
    t.setStyle(TableStyle(style))
    story.append(t)


def _fuss(story, s, extra: str = ""):
    story.append(Spacer(1, 12))
    txt = ("Berechnung nach WMZ-Heizschlüssel, EnBW-Strompreis "
           f"{_eur(cfg.STROMPREIS_EUR_KWH)}/kWh und den amtlichen Wasser- bzw. "
           "Niederschlagswassergebühren. Warmwasser-Heizenergie über den "
           f"Gerätekennwert {cfg.WW_KWH_PRO_M3:.1f} kWh/m³. ")
    story.append(Paragraph(txt + extra, s["small"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Erstellt am {date.today():%d.%m.%Y} · {cfg.OBJEKT['adresse']}", s["small"]))


def _doc(pfad: Path) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        str(pfad), pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title="Nebenkostenabrechnung", author="NK-Abrechnungsprogramm",
    )


def abrechnung_pdf(ab: e.Abrechnung, pfad: str | Path,
                   saldo_label: str = "Saldo", hinweis: str = "") -> Path:
    """Erzeugt ein PDF für eine einzelne Perioden-Abrechnung."""
    pfad = Path(pfad)
    s = _styles()
    story = []
    _kopf(story, s, ab.titel, ab.mieter, ab.zeitraum)
    _positions_tabelle(story, s, ab, saldo_label)
    if hinweis:
        story.append(Spacer(1, 8))
        story.append(Paragraph(hinweis, s["small"]))
    _fuss(story, s)
    _doc(pfad).build(story)
    return pfad


def eigentuemer_pdf(es: e.EigentuemerSaldo, pfad: str | Path) -> Path:
    """Eigentümer-interner Zwischenstand Thomas ↔ Christine Weis."""
    pfad = Path(pfad)
    s = _styles()
    story = []
    _kopf(story, s, "Eigentümer-interne Abrechnung (Zwischenstand)",
          "Thomas Weis → Christine Weis",
          f"Stand {date.today():%d.%m.%Y}")

    rows = [["Position", "Betrag"]]
    for bez, betrag in es.positionen:
        rows.append([bez, _eur(betrag)])
    r_sum = len(rows)
    rows.append(["Zwischensumme Kosten", _eur(es.summe_positionen)])
    rows.append(["Sonderzahlungen Thomas → Christine", _eur(es.sonderzahlungen)])
    rows.append(["Saldo aus früherer Abrechnung (bez. 03/2026)", _eur(es.saldo_alt)])
    r_saldo = len(rows)
    rows.append(["Zwischensaldo", _eur(es.zwischensaldo)])

    style = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, len(es.positionen)), [colors.white, LIGHT]),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, r_sum), (-1, r_sum), "Helvetica-Bold"),
        ("LINEABOVE", (0, r_sum), (-1, r_sum), 0.8, PRIMARY),
        ("FONTNAME", (0, r_saldo), (-1, r_saldo), "Helvetica-Bold"),
        ("FONTSIZE", (0, r_saldo), (-1, r_saldo), 11),
        ("BACKGROUND", (0, r_saldo), (-1, r_saldo), PRIMARY),
        ("TEXTCOLOR", (0, r_saldo), (-1, r_saldo), colors.white),
    ]
    t = Table(rows, colWidths=[120 * mm, 50 * mm])
    t.setStyle(TableStyle(style))
    story.append(t)

    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"Kulanz: Der Warmwasser-Verbrauch der EG-Wohnung (Christine, "
        f"Eigennutzung) im Wert von {_eur(es.ww_eg_erlassen)} wird von Thomas "
        f"erlassen und ist hier nicht enthalten.", s["small"]))

    story.append(Paragraph("Offene Punkte", s["h2"]))
    for p in es.offene_punkte:
        story.append(Paragraph(f"•&nbsp; {p}", s["small"]))

    _fuss(story, s)
    _doc(pfad).build(story)
    return pfad


def verbrauchsuebersicht_pdf(pfad: str | Path) -> Path:
    """Verbrauchs- und Plausibilitätsübersicht (COP-Prüfung)."""
    pfad = Path(pfad)
    s = _styles()
    story = [Paragraph("Verbrauchs- und Plausibilitätsübersicht", s["title"]),
             Paragraph(cfg.OBJEKT["adresse"], s["sub"])]

    # Zählerstände
    story.append(Paragraph("Zählerstände", s["h2"]))
    kopf = ["Zähler", "Nr.", "Feb 2024", "Mai 2025", "Jun 2026", "Einheit"]
    rows = [kopf]
    for m in cfg.METERS.values():
        def g(t):
            return f"{m.staende[t]:.3f}" if t in m.staende else "–"
        rows.append([m.beschreibung, m.serial_no,
                     g(cfg.STICHTAG_START), g(cfg.STICHTAG_MITTE),
                     g(cfg.STICHTAG_ENDE), m.einheit])
    t = Table(rows, colWidths=[46 * mm, 24 * mm, 24 * mm, 24 * mm, 24 * mm, 18 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (2, 0), (4, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)

    # Heizschlüssel & COP
    story.append(Paragraph("Heizschlüssel & COP-Plausibilität", s["h2"]))
    pug1 = e.heizschluessel_ug(cfg.STICHTAG_START, cfg.STICHTAG_MITTE)
    pug2 = e.heizschluessel_ug(cfg.STICHTAG_MITTE, cfg.STICHTAG_ENDE)
    cop2 = e.cop(cfg.STICHTAG_MITTE, cfg.STICHTAG_ENDE)
    cop1 = e.cop(cfg.STICHTAG_START, cfg.STICHTAG_MITTE)
    rows = [
        ["Periode", "UG-Anteil (pug)", "COP", "Plausibilität"],
        ["Feb 2024 – Mai 2025 (P1)", f"{pug1*100:.2f} %", f"{cop1:.2f}",
         "plausibel" if 1.5 <= cop1 <= 6 else "prüfen"],
        ["Mai 2025 – Jun 2026 (Leer+P2)", f"{pug2*100:.2f} %", f"{cop2:.2f}",
         "plausibel" if 1.5 <= cop2 <= 6 else "prüfen"],
    ]
    t = Table(rows, colWidths=[62 * mm, 34 * mm, 24 * mm, 40 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Hinweis: Die März-2026-Ablesung (WMZ) wurde verworfen, da die "
        "COP-Prüfung ein falsches Register ergab (COP 0,62 bzw. 7,94 – "
        "physikalisch unmöglich). Es wird nur mit den drei belastbaren "
        "Stichtagen gerechnet.", s["small"]))

    _fuss(story, s)
    _doc(pfad).build(story)
    return pfad

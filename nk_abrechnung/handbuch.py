"""Übergabe-Handbuch (PDF) für den neuen Eigentümer.

Eigenständiges, ausführliches Dokument – unabhängig von README.md – das
die App Schritt für Schritt erklärt: Einrichtung (lokal + Cloud), tägliche
Nutzung, die jährliche Abrechnung mit der zweiten Partei, offene Punkte
und Problembehebung. Richtet sich an jemanden ohne Programmierkenntnisse.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, HRFlowable,
)

from . import config as cfg

PRIMARY = colors.HexColor("#1f3a5f")
LIGHT = colors.HexColor("#eef2f7")
MUTED = colors.HexColor("#555555")
ACCENT = colors.HexColor("#c0392b")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle("ct", parent=base["Title"], fontSize=26,
                                      textColor=PRIMARY, spaceAfter=6, leading=30),
        "cover_sub": ParagraphStyle("cs", parent=base["Normal"], fontSize=13,
                                    textColor=MUTED, spaceAfter=4, leading=18),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=16,
                             textColor=PRIMARY, spaceBefore=4, spaceAfter=10),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=12.5,
                             textColor=PRIMARY, spaceBefore=12, spaceAfter=6),
        "body": ParagraphStyle("b", parent=base["Normal"], fontSize=10,
                               leading=15, spaceAfter=6),
        "small": ParagraphStyle("sm", parent=base["Normal"], fontSize=8.5,
                                textColor=MUTED, leading=12),
        "step": ParagraphStyle("st", parent=base["Normal"], fontSize=10,
                               leading=15, spaceAfter=4),
        "warn": ParagraphStyle("w", parent=base["Normal"], fontSize=10,
                               leading=15, textColor=ACCENT, spaceAfter=6),
        "code": ParagraphStyle("code", parent=base["Normal"], fontName="Courier",
                               fontSize=9, textColor=PRIMARY, backColor=LIGHT,
                               leading=13, leftIndent=8, spaceAfter=6, spaceBefore=2),
    }


def _hr(story):
    story.append(HRFlowable(width="100%", thickness=0.6,
                            color=colors.HexColor("#cccccc"), spaceBefore=6, spaceAfter=10))


def _nummeriert(story, s, punkte: list[str]):
    items = [ListItem(Paragraph(p, s["step"]), leftIndent=14, bulletColor=PRIMARY)
             for p in punkte]
    story.append(ListFlowable(items, bulletType="1", start=1, leftIndent=12))


def _bullets(story, s, punkte: list[str]):
    items = [ListItem(Paragraph(p, s["step"]), leftIndent=14, bulletColor=PRIMARY)
             for p in punkte]
    story.append(ListFlowable(items, bulletType="bullet", leftIndent=12))


def handbuch_pdf(pfad: str | Path) -> Path:
    pfad = Path(pfad)
    s = _styles()
    story: list = []

    # -- Deckblatt --------------------------------------------------------
    story.append(Spacer(1, 60 * mm))
    story.append(Paragraph("Übergabe-Handbuch", s["cover_title"]))
    story.append(Paragraph("NK-Abrechnungsprogramm", s["cover_title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(cfg.OBJEKT["adresse"], s["cover_sub"]))
    story.append(Paragraph(f"Für: {cfg.NEUER_EIGENTUEMER_NAME}", s["cover_sub"]))
    story.append(Paragraph(f"Zweite Partei: {cfg.ZWEITE_PARTEI_NAME}", s["cover_sub"]))
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"Stand: {date.today():%d.%m.%Y}", s["small"]))
    story.append(PageBreak())

    # -- 1. Überblick -------------------------------------------------------
    story.append(Paragraph("1. Überblick", s["h1"]))
    story.append(Paragraph(
        "Dieses Programm berechnet die Nebenkostenabrechnung für das Objekt "
        f"{cfg.OBJEKT['adresse']} und die laufende Verrechnung zwischen den "
        "beiden Eigentümerparteien. Es übernimmt die komplette Rechenarbeit "
        "aus den Roh-Zählerständen (Strom, Wärmemenge, Wasser) und den "
        "hinterlegten Kostensätzen – nichts ist von Hand nachzurechnen.",
        s["body"]))
    story.append(Paragraph(
        "Die App läuft im Web-Browser (auch auf dem Handy) und bietet:",
        s["body"]))
    _bullets(story, s, [
        "Zähler per Foto ablesen (Zählerstand wird automatisch vorgeschlagen)",
        "Eingangsrechnungen (Strom, Wasser, Versicherung, Grundsteuer, …) als "
        "Foto oder PDF hinterlegen",
        "Fertige Nebenkostenabrechnungen als PDF erzeugen",
        "Die eigentümerinterne Verrechnung mit der zweiten Partei einsehen",
    ])
    story.append(Paragraph(
        "<b>Wichtig:</b> Beide Parteien sollen jederzeit dieselben Daten sehen "
        "und ergänzen können. Dafür nutzt die App eine gemeinsame "
        "Cloud-Datenbank (Abschnitt 3) statt einer Datei auf nur einem Rechner.",
        s["body"]))

    story.append(Paragraph("2. Objekt & Parteien", s["h1"]))
    obj_label = ParagraphStyle("objl", parent=s["body"], fontSize=9.5, leading=13,
                               fontName="Helvetica-Bold", spaceAfter=0)
    obj_val = ParagraphStyle("objv", parent=s["body"], fontSize=9.5, leading=13,
                             spaceAfter=0)
    rows = [
        ["Adresse", cfg.OBJEKT["adresse"]],
        ["UG (vermietet)", f"{cfg.OBJEKT['flaeche_ug_m2']:.0f} m² "
                           f"({cfg.UG_ANTEIL*100:.2f} % der Gesamtfläche)"],
        ["EG (Eigennutzung)", f"{cfg.OBJEKT['flaeche_eg_m2']:.0f} m²"],
        ["Eigentümer aktuell", f"{cfg.NEUER_EIGENTUEMER_NAME} / {cfg.ZWEITE_PARTEI_NAME}"],
        ["Wärmeerzeugung", "Luft-Wasser-Wärmepumpe (Mitsubishi) mit "
                           "Wärmemengenzählern UG/EG"],
    ]
    tabellen_rows = [[Paragraph(a, obj_label), Paragraph(b, obj_val)] for a, b in rows]
    t = Table(tabellen_rows, colWidths=[45 * mm, 120 * mm])
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
    ]))
    story.append(t)
    story.append(Paragraph(
        f"<b>Wichtiger Hinweis zur Übergabe:</b> Abgeschlossene, historische "
        f"Abrechnungen (Mieter Felix Adameck, Leerstand, Fam. Beltz bis zum "
        f"Eigentümerwechsel) bleiben unverändert Thomas Weis zugeordnet, da "
        f"sie in dessen Eigentumszeit fielen. Der Name des neuen Eigentümers "
        f"wird in <font face='Courier'>nk_abrechnung/config.py</font> "
        f"(Konstante <font face='Courier'>NEUER_EIGENTUEMER_NAME</font>) "
        f"einmalig eingetragen, sobald er feststeht – danach erscheint er "
        f"automatisch in der App und in allen künftigen PDFs.", s["body"]))
    story.append(PageBreak())

    # -- 3. Einrichtung -------------------------------------------------------
    story.append(Paragraph("3. Einrichtung (einmalig)", s["h1"]))
    story.append(Paragraph(
        "Es gibt zwei Betriebsarten. Für die gemeinsame Nutzung durch beide "
        "Parteien wird <b>Variante B</b> empfohlen.", s["body"]))

    story.append(Paragraph("3.1 Variante A – Lokal im WLAN (einfach, nur ein Gerät)",
                           s["h2"]))
    story.append(Paragraph(
        "Geeignet zum Ausprobieren oder wenn nur eine Person am selben "
        "Rechner arbeitet. Python und die Programmbibliotheken müssen auf "
        "einem Rechner installiert sein.", s["body"]))
    _nummeriert(story, s, [
        "Terminal öffnen, in den Projektordner wechseln.",
        "Einmalig: <font face='Courier'>pip install -r requirements.txt</font>",
        "Start: <font face='Courier'>./start_mobile.sh</font>",
        "Die angezeigte Adresse (z.B. http://192.168.1.23:8501) im Browser "
        "des Handys öffnen (gleiches WLAN vorausgesetzt).",
    ])

    story.append(Paragraph("3.2 Variante B – Gemeinsame Cloud-App (empfohlen)",
                           s["h2"]))
    story.append(Paragraph(
        "Feste Web-Adresse, von überall erreichbar, beide Parteien sehen "
        "dieselben Daten dauerhaft. Benötigt zwei kostenlose Konten: "
        "Supabase (Datenbank) und Streamlit Community Cloud (Hosting).",
        s["body"]))

    story.append(Paragraph("<b>Schritt A – Datenbank bei Supabase anlegen:</b>", s["body"]))
    _nummeriert(story, s, [
        "Auf supabase.com kostenloses Konto anlegen, neues Projekt erstellen "
        "(Name frei wählbar, z.B. \"nk-teinacher\").",
        "Ein Datenbank-Passwort vergeben und sicher notieren.",
        "Nach dem Anlegen: Project Settings → Database → Connection string → "
        "URI. Diese Zeichenfolge kopieren.",
    ])
    story.append(Paragraph(
        "postgresql://postgres:PASSWORT@db.xxxxxxxx.supabase.co:5432/postgres",
        s["code"]))

    story.append(Paragraph("<b>Schritt B – App bei Streamlit Cloud veröffentlichen:</b>",
                           s["body"]))
    story.append(Paragraph(
        "Die Secrets aus Punkt 3 unten (Passwort frei wählen, DATABASE_URL "
        "aus Schritt A einsetzen) sehen so aus:", s["body"]))
    story.append(Paragraph(
        'app_password = "ein-sicheres-passwort"<br/>'
        'DATABASE_URL = "postgresql://postgres:PASSWORT@db.xxxxxxxx.supabase.co:5432/postgres"',
        s["code"]))
    _nummeriert(story, s, [
        "Auf share.streamlit.io mit dem GitHub-Konto anmelden, \"New app\" wählen.",
        "Repository, Branch <font face='Courier'>main</font> und Hauptdatei "
        "<font face='Courier'>streamlit_app.py</font> auswählen.",
        "Unter \"Advanced settings → Secrets\" die obigen beiden Zeilen eintragen.",
        "\"Deploy\" klicken. Nach ca. 1 Minute ist die App unter einer "
        "eigenen Adresse (…streamlit.app) erreichbar.",
        "Diese Adresse an beide Parteien weitergeben und als Lesezeichen "
        "speichern (PC und Handy).",
    ])
    story.append(Paragraph(
        "Beim ersten Öffnen fragt die App nach dem Passwort (Schritt B.3) – "
        "danach sind alle Bereiche nutzbar.", s["body"]))
    story.append(PageBreak())

    # -- 4. Tägliche Nutzung -------------------------------------------------
    story.append(Paragraph("4. Tägliche / laufende Nutzung", s["h1"]))

    story.append(Paragraph("4.1 Zähler ablesen", s["h2"]))
    _nummeriert(story, s, [
        "Bereich \"Zähler ablesen\" öffnen.",
        "Zähler aus der Liste wählen (z.B. \"WP-Strom\", \"WMZ UG\").",
        "Foto hochladen oder direkt mit der Handykamera aufnehmen.",
        "Der erkannte Zählerstand wird vorgeschlagen (falls OCR aktiv, siehe "
        "Abschnitt 5) – bei Bedarf korrigieren.",
        "Unter \"Erfasst von\" den eigenen Namen auswählen.",
        "\"Ablesung speichern\" klicken.",
    ])
    story.append(Paragraph(
        "Die App warnt automatisch, wenn ein neuer Wert kleiner als die "
        "letzte Ablesung ist (möglicher Zahlendreher).", s["body"]))

    story.append(Paragraph("4.2 Rechnungsbelege erfassen", s["h2"]))
    story.append(Paragraph(
        "Viele Rechnungen (Strom, Wasser, Versicherung, Grundsteuer) gehen "
        "bei der zweiten Partei ein. Im Bereich \"Belege\" erfasst, sind "
        "sie sofort für beide Seiten dokumentiert – unabhängig davon, wer "
        "das Papier in der Hand hält.", s["body"]))
    _nummeriert(story, s, [
        "Bereich \"Belege\" → Reiter \"Beleg erfassen\".",
        "Kategorie wählen (Strom, Wasser, Versicherung, Grundsteuer, "
        "Niederschlagswasser, Sonstiges).",
        "Lieferant, Rechnungsdatum, Zeitraum und \"Erfasst von\" ausfüllen.",
        "Foto oder PDF der Rechnung hochladen – der Betrag wird bei Fotos "
        "automatisch vorgeschlagen (falls OCR aktiv).",
        "\"Beleg speichern\" klicken.",
    ])
    story.append(Paragraph(
        "Im Reiter \"Belegübersicht\" sind alle Belege mit Summen je "
        "Kategorie einsehbar – praktisch für den Jahresüberblick.", s["body"]))
    story.append(PageBreak())

    # -- 5. OCR ---------------------------------------------------------------
    story.append(Paragraph("5. Automatische Zahlenerkennung (OCR) – optional", s["h1"]))
    story.append(Paragraph(
        "Die App funktioniert auch komplett ohne automatische Erkennung – "
        "Zählerstand bzw. Betrag werden dann von Hand eingetragen, das Foto "
        "dient trotzdem als Nachweis. Für die Komforterkennung:", s["body"]))
    _bullets(story, s, [
        "<b>Claude Vision</b> (empfohlen, beste Erkennungsqualität): "
        "Umgebungsvariable bzw. Secret <font face='Courier'>ANTHROPIC_API_KEY</font> "
        "mit einem Anthropic-API-Schlüssel setzen.",
        "<b>Tesseract</b> (kostenlos, lokal): Systempaket "
        "<font face='Courier'>tesseract-ocr</font> installieren, zusätzlich "
        "<font face='Courier'>pip install pytesseract</font>.",
    ])
    story.append(Paragraph(
        "In der Seitenleiste zeigt die App an, welches Backend gerade aktiv ist.",
        s["body"]))

    # -- 6. Jährliche Abrechnung ------------------------------------------
    story.append(Paragraph("6. Jährliche Abrechnung mit der zweiten Partei", s["h1"]))
    story.append(Paragraph(
        "Die Nebenkostenabrechnung läuft über das Kalender-/Mietjahr. Am "
        "Ende einer Abrechnungsperiode:", s["body"]))
    _nummeriert(story, s, [
        "Sicherstellen, dass alle relevanten Zählerstände zum Stichtag "
        "erfasst sind (Bereich \"Zähler ablesen\").",
        "Sicherstellen, dass alle Rechnungen des Zeitraums als Beleg "
        "hinterlegt sind (Bereich \"Belege\").",
        "Bereich \"Verbrauch & COP\" prüfen: der COP-Wert (Verhältnis "
        "erzeugte Wärme zu eingesetztem Strom) muss plausibel sein "
        "(üblich: 2 bis 5). Ein unplausibler Wert deutet auf einen "
        "Ablesefehler hin – betroffene Stände dann nicht verwenden "
        "(siehe Beispiel März 2026 in der Berechnungsmethodik, README).",
        "Bereich \"Abrechnung\" öffnen: Ergebnisse je Partei prüfen und "
        "als PDF herunterladen.",
        "Abschnitt \"Eigentümer-intern\" zeigt den Verrechnungsstand mit der "
        "zweiten Partei – ebenfalls als PDF verfügbar.",
    ])
    story.append(Paragraph(
        "Die Berechnungsformeln (Heizschlüssel, Warmwasser-Heizenergie, "
        "Wasser-/Niederschlagsanteile) sind in README.md, Abschnitt "
        "\"Berechnungsmethodik\", im Detail erklärt und im Code "
        "(<font face='Courier'>nk_abrechnung/engine.py</font>) nachvollziehbar "
        "– es wird nichts verdeckt \"geschätzt\".", s["body"]))
    story.append(PageBreak())

    # -- 7. Offene Punkte -----------------------------------------------------
    story.append(Paragraph("7. Offene Punkte zur Übergabe (Checkliste)", s["h1"]))
    _bullets(story, s, [
        "<b>Name des neuen Eigentümers</b> in "
        "<font face='Courier'>nk_abrechnung/config.py</font> eintragen "
        "(Konstante <font face='Courier'>NEUER_EIGENTUEMER_NAME</font>).",
        "<b>DATABASE_URL</b> (Supabase) einrichten, damit beide Parteien "
        "dieselben Daten sehen (siehe Abschnitt 3.2) – ohne diesen Schritt "
        "gehen in der Cloud erfasste Daten bei einem Neustart verloren.",
        "<b>Übergabe-Zählerstände</b> zum Stichtag des Eigentümerwechsels "
        "ablesen und erfassen – das ist die neue Ausgangsbasis.",
        "Offene Frage aus der laufenden Abrechnung: ab welchem Monat wurde "
        "die monatliche Zahlung von 195 € auf 240 € angehoben? Für die "
        "abschließende Verrechnung der historischen Periode zu klären.",
        "Finale EnBW-Jahresrechnung zur Verifizierung des Stromgrundpreises "
        "abwarten und mit den hinterlegten Werten abgleichen.",
    ])

    story.append(Paragraph("8. Problembehebung (FAQ)", s["h1"]))
    faq_cell = ParagraphStyle("faq", parent=s["body"], fontSize=9, leading=12, spaceAfter=0)
    faq_head = ParagraphStyle("faqh", parent=faq_cell, textColor=colors.white,
                              fontName="Helvetica-Bold")
    rows = [
        ["App zeigt \"Lokale Datenbank\" statt \"Geteilte Cloud-Datenbank\"",
         "DATABASE_URL fehlt oder ist falsch – in den Secrets prüfen (Abschnitt 3.2)."],
        ["Passwort vergessen", "In den Streamlit-Cloud-Secrets unter "
                               "app_password nachsehen bzw. neu setzen."],
        ["OCR erkennt den Wert nicht richtig", "Wert einfach manuell korrigieren "
                                               "– das Foto bleibt trotzdem als Nachweis gespeichert."],
        ["Foto lässt sich nicht hochladen", "Dateigröße/-format prüfen "
                                            "(JPG, PNG, bei Belegen zusätzlich PDF)."],
        ["Unklar, wer einen Wert erfasst hat", "Spalte \"Erfasst von\" in den "
                                               "Übersichten (Ablesungen, Belege) prüfen."],
    ]
    kopf = [Paragraph("Problem", faq_head), Paragraph("Lösung", faq_head)]
    body_rows = [[Paragraph(a, faq_cell), Paragraph(b, faq_cell)] for a, b in rows]
    t = Table([kopf] + body_rows, colWidths=[70 * mm, 95 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    story.append(Spacer(1, 14))
    _hr(story)
    story.append(Paragraph(
        "Weiterführende technische Dokumentation (Formeln, Projektstruktur, "
        "Testergebnisse): README.md im Projekt-Repository.", s["small"]))
    story.append(Paragraph(f"Erstellt am {date.today():%d.%m.%Y} · "
                           f"{cfg.OBJEKT['adresse']}", s["small"]))

    doc = SimpleDocTemplate(
        str(pfad), pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title="Übergabe-Handbuch NK-Abrechnung", author="NK-Abrechnungsprogramm",
    )
    doc.build(story)
    return pfad

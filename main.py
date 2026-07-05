#!/usr/bin/env python3
"""NK-Abrechnungsprogramm – Kommandozeilen-Einstieg.

Teinacher Str. 4, 75387 Neubulach.

Beispiele:
    python main.py rechnen          # Ergebnisse in der Konsole
    python main.py pdf              # alle PDFs nach ./output erzeugen
    python main.py db               # SQLite-Datenbank aufbauen + seeden
    python main.py alles            # DB + PDFs + Konsolenausgabe
"""

from __future__ import annotations

import argparse
from pathlib import Path

from nk_abrechnung import config as cfg
from nk_abrechnung import engine as e
from nk_abrechnung import database, pdf

OUTPUT = Path(__file__).parent / "output"


def _eur(v: float) -> str:
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def cmd_rechnen(_args) -> None:
    print(f"\nNK-Abrechnung – {cfg.OBJEKT['adresse']}\n" + "=" * 60)
    pug1 = e.heizschluessel_ug(cfg.STICHTAG_START, cfg.STICHTAG_MITTE)
    pug2 = e.heizschluessel_ug(cfg.STICHTAG_MITTE, cfg.STICHTAG_ENDE)
    print(f"Heizschlüssel UG  P1: {pug1*100:5.2f} %   "
          f"P2: {pug2*100:5.2f} %")
    print(f"COP-Plausibilität P1: {e.cop(cfg.STICHTAG_START, cfg.STICHTAG_MITTE):.2f}"
          f"    Leer+P2: {e.cop(cfg.STICHTAG_MITTE, cfg.STICHTAG_ENDE):.2f}")

    for a in e.alle_abrechnungen().values():
        print("\n" + "-" * 60)
        print(f"{a.titel}: {a.mieter}")
        print(f"Zeitraum: {a.zeitraum}")
        for bez, betrag in a.positionen:
            print(f"  {bez:<38}{_eur(betrag):>14}")
        for bez, betrag in a.zusatz:
            print(f"  {bez:<38}{_eur(betrag):>14}")
        print(f"  {'SOLL':<38}{_eur(a.soll):>14}")
        print(f"  {'IST (geleistet)':<38}{_eur(a.ist_zahlung):>14}")
        vorz = "Nachzahlung" if a.saldo >= 0 else "Guthaben"
        print(f"  {vorz:<38}{_eur(abs(a.saldo)):>14}")

    es = e.eigentuemer_zwischenstand()
    print("\n" + "-" * 60)
    print("Eigentümer-intern Thomas → Christine (Zwischenstand)")
    for bez, betrag in es.positionen:
        print(f"  {bez:<38}{_eur(betrag):>14}")
    print(f"  {'Zwischensaldo':<38}{_eur(es.zwischensaldo):>14}")
    print(f"  WW-EG erlassen (Kulanz): {_eur(es.ww_eg_erlassen)}")
    print("  Offene Punkte:")
    for p in es.offene_punkte:
        print(f"    - {p}")
    print()


def cmd_pdf(_args) -> None:
    OUTPUT.mkdir(exist_ok=True)
    ab = e.alle_abrechnungen()
    ergebnisse = [
        pdf.abrechnung_pdf(ab["P1"], OUTPUT / "NK_Felix_Adameck.pdf",
                           saldo_label="Ergebnis",
                           hinweis="Frist §556 Abs. 3 BGB: 30.04.2026."),
        pdf.abrechnung_pdf(ab["P2"], OUTPUT / "NK_Beltz_Abschluss.pdf",
                           saldo_label="Ergebnis"),
        pdf.abrechnung_pdf(ab["LEER"], OUTPUT / "NK_Leerstand_Thomas.pdf",
                           saldo_label="von Thomas zu tragen"),
        pdf.eigentuemer_pdf(e.eigentuemer_zwischenstand(),
                            OUTPUT / "NK_Christine_Weis_Zwischenstand.pdf"),
        pdf.verbrauchsuebersicht_pdf(OUTPUT / "NK_Verbrauchsuebersicht.pdf"),
    ]
    print("PDFs erzeugt:")
    for p in ergebnisse:
        print(f"  {p}")


def cmd_db(_args) -> None:
    OUTPUT.mkdir(exist_ok=True)
    path = database.build(OUTPUT / "nk_teinacher.db", overwrite=True)
    print(f"Datenbank aufgebaut: {path}")


def cmd_alles(args) -> None:
    cmd_db(args)
    cmd_pdf(args)
    cmd_rechnen(args)


def main() -> None:
    parser = argparse.ArgumentParser(description="NK-Abrechnung Teinacher Str. 4")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("rechnen", help="Ergebnisse in der Konsole anzeigen")
    sub.add_parser("pdf", help="alle PDF-Abrechnungen erzeugen")
    sub.add_parser("db", help="SQLite-Datenbank aufbauen und seeden")
    sub.add_parser("alles", help="DB + PDFs + Konsolenausgabe")
    args = parser.parse_args()

    handlers = {"rechnen": cmd_rechnen, "pdf": cmd_pdf,
                "db": cmd_db, "alles": cmd_alles}
    handlers.get(args.cmd, cmd_rechnen)(args)


if __name__ == "__main__":
    main()

"""Streamlit-Oberfläche: Zähler-Ablesung per Foto + NK-Abrechnung.

Teinacher Str. 4, 75387 Neubulach.

Start:
    streamlit run streamlit_app.py

Fotos werden unter ``output/photos`` abgelegt, Ablesungen in der SQLite-
Datenbank ``output/nk_teinacher.db`` gespeichert. Der Zählerstand wird –
sofern ein OCR-Backend verfügbar ist (Claude Vision oder Tesseract) –
automatisch vorgeschlagen und vom Nutzer bestätigt.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st

from nk_abrechnung import config as cfg
from nk_abrechnung import engine as e
from nk_abrechnung import database, ocr, pdf

BASE = Path(__file__).parent
OUTPUT = BASE / "output"
PHOTOS = OUTPUT / "photos"
DB_PATH = OUTPUT / "nk_teinacher.db"


def _eur(v: float) -> str:
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


@st.cache_resource
def get_db_path() -> str:
    OUTPUT.mkdir(exist_ok=True)
    PHOTOS.mkdir(exist_ok=True)
    return str(database.build(DB_PATH))


def con():
    return database.connect(get_db_path())


st.set_page_config(page_title="NK-Abrechnung Teinacher Str. 4",
                   page_icon="🏠", layout="wide")

st.sidebar.title("🏠 NK-Abrechnung")
st.sidebar.caption(cfg.OBJEKT["adresse"])
seite = st.sidebar.radio(
    "Navigation",
    ["📷 Zähler ablesen", "📋 Ablesungen", "🧾 Abrechnung",
     "📊 Verbrauch & COP", "ℹ️ Status"],
)

backends = ocr.available_backends()
if backends:
    st.sidebar.success("OCR aktiv: " + ", ".join(backends))
else:
    st.sidebar.info("Kein OCR-Backend – Werte manuell eingeben.\n\n"
                    "Aktivierbar über `ANTHROPIC_API_KEY` (Claude Vision) "
                    "oder Installation von Tesseract.")


# ---------------------------------------------------------------------------
# 📷 Zähler ablesen
# ---------------------------------------------------------------------------
if seite == "📷 Zähler ablesen":
    st.header("📷 Zähler ablesen")
    c = con()
    meters = database.list_meters(c)
    labels = {f"{m['description']} ({m['serial_no']}) [{m['unit']}]": m for m in meters}

    col1, col2 = st.columns(2)
    with col1:
        wahl = st.selectbox("Zähler", list(labels))
        meter = labels[wahl]
        ablesedatum = st.date_input("Ablesedatum", value=date.today())
    with col2:
        quelle = st.radio("Foto-Quelle", ["Hochladen", "Kamera"], horizontal=True)
        if quelle == "Kamera":
            bild = st.camera_input("Zähler fotografieren")
        else:
            bild = st.file_uploader("Zählerfoto", type=["jpg", "jpeg", "png"])

    vorschlag = st.session_state.get("ocr_value")
    foto_pfad = None

    if bild is not None:
        st.image(bild, caption="Zählerfoto", width=360)
        ext = Path(getattr(bild, "name", "foto.png")).suffix or ".png"
        foto_pfad = PHOTOS / f"{meter['serial_no']}_{ablesedatum.isoformat()}{ext}"
        foto_pfad.write_bytes(bild.getvalue())

        if backends and st.button("🔍 Zählerstand per OCR erkennen"):
            with st.spinner("OCR läuft …"):
                res = ocr.read_meter(foto_pfad)
            if res.value is not None:
                st.session_state["ocr_value"] = res.value
                vorschlag = res.value
                st.success(f"Erkannt ({res.backend}): {res.value}")
            else:
                st.warning(res.note or "Kein Wert erkannt – bitte manuell eingeben.")
            if res.raw_text:
                st.caption(f"Rohtext: {res.raw_text}")

    wert = st.number_input(
        f"Zählerstand [{meter['unit']}]",
        value=float(vorschlag) if vorschlag is not None else 0.0,
        step=0.001, format="%.3f",
    )

    # Plausibilität: Vergleich mit letzter Ablesung.
    vorherige = database.list_readings(c, meter["id"])
    if vorherige:
        letzte = max(vorherige, key=lambda r: r["date"])
        if wert and wert < letzte["value"]:
            st.warning(f"⚠️ Wert kleiner als letzte Ablesung "
                       f"({letzte['value']} am {letzte['date']}). Bitte prüfen.")

    if st.button("💾 Ablesung speichern", type="primary", disabled=(wert <= 0)):
        database.add_reading(c, meter["id"], ablesedatum.isoformat(), float(wert),
                             str(foto_pfad) if foto_pfad else None)
        st.session_state.pop("ocr_value", None)
        st.success(f"Gespeichert: {meter['description']} = {wert} {meter['unit']} "
                   f"({ablesedatum.isoformat()})")
    c.close()


# ---------------------------------------------------------------------------
# 📋 Ablesungen
# ---------------------------------------------------------------------------
elif seite == "📋 Ablesungen":
    st.header("📋 Erfasste Ablesungen")
    c = con()
    readings = database.list_readings(c)
    c.close()
    if not readings:
        st.info("Noch keine Ablesungen erfasst.")
    else:
        tabelle = [{"Datum": r["date"], "Zähler": r["description"],
                    "Nr.": r["serial_no"], "Wert": r["value"],
                    "Einheit": r["unit"], "Foto": "📎" if r["photo_path"] else ""}
                   for r in readings]
        st.dataframe(tabelle, width="stretch", hide_index=True)

        mit_foto = [r for r in readings if r["photo_path"] and Path(r["photo_path"]).exists()]
        if mit_foto:
            st.subheader("Fotonachweise")
            cols = st.columns(4)
            for i, r in enumerate(mit_foto):
                with cols[i % 4]:
                    st.image(r["photo_path"],
                             caption=f"{r['description']} · {r['date']}",
                             width="stretch")


# ---------------------------------------------------------------------------
# 🧾 Abrechnung
# ---------------------------------------------------------------------------
elif seite == "🧾 Abrechnung":
    st.header("🧾 Nebenkostenabrechnung")
    OUTPUT.mkdir(exist_ok=True)

    ab = e.alle_abrechnungen()
    reihen = [("P1", ab["P1"], "Ergebnis"),
              ("LEER", ab["LEER"], "von Thomas zu tragen"),
              ("P2", ab["P2"], "Ergebnis")]

    cols = st.columns(3)
    for col, (_, a, _lbl) in zip(cols, reihen):
        with col:
            st.metric(a.mieter.split("(")[0].strip(),
                      _eur(a.soll),
                      f"{'Nachzahlung' if a.saldo >= 0 else 'Guthaben'} {_eur(abs(a.saldo))}",
                      delta_color="inverse")

    for key, a, lbl in reihen:
        with st.expander(f"{a.titel} – {a.mieter} ({a.zeitraum})"):
            st.table([{"Position": b, "Betrag": _eur(v)} for b, v in a.positionen]
                     + [{"Position": b, "Betrag": _eur(v)} for b, v in a.zusatz]
                     + [{"Position": "SOLL", "Betrag": _eur(a.soll)},
                        {"Position": "IST", "Betrag": _eur(a.ist_zahlung)},
                        {"Position": lbl, "Betrag": _eur(a.saldo)}])
            dateiname = {"P1": "NK_Felix_Adameck.pdf", "LEER": "NK_Leerstand_Thomas.pdf",
                         "P2": "NK_Beltz_Abschluss.pdf"}[key]
            pfad = pdf.abrechnung_pdf(a, OUTPUT / dateiname, saldo_label=lbl)
            st.download_button("📄 PDF herunterladen", Path(pfad).read_bytes(),
                               file_name=dateiname, mime="application/pdf", key=key)

    st.subheader("Eigentümer-intern (Thomas → Christine)")
    es = e.eigentuemer_zwischenstand()
    st.table([{"Position": b, "Betrag": _eur(v)} for b, v in es.positionen]
             + [{"Position": "Zwischensaldo", "Betrag": _eur(es.zwischensaldo)}])
    st.caption(f"Kulanz WW-EG erlassen: {_eur(es.ww_eg_erlassen)}")
    for p in es.offene_punkte:
        st.warning("Offen: " + p)
    epfad = pdf.eigentuemer_pdf(es, OUTPUT / "NK_Christine_Weis_Zwischenstand.pdf")
    st.download_button("📄 Eigentümer-PDF", Path(epfad).read_bytes(),
                       file_name="NK_Christine_Weis_Zwischenstand.pdf",
                       mime="application/pdf")


# ---------------------------------------------------------------------------
# 📊 Verbrauch & COP
# ---------------------------------------------------------------------------
elif seite == "📊 Verbrauch & COP":
    st.header("📊 Verbrauch & COP-Plausibilität")

    pug1 = e.heizschluessel_ug(cfg.STICHTAG_START, cfg.STICHTAG_MITTE)
    pug2 = e.heizschluessel_ug(cfg.STICHTAG_MITTE, cfg.STICHTAG_ENDE)
    cop1 = e.cop(cfg.STICHTAG_START, cfg.STICHTAG_MITTE)
    cop2 = e.cop(cfg.STICHTAG_MITTE, cfg.STICHTAG_ENDE)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Heizschlüssel UG P1", f"{pug1*100:.2f} %")
    c2.metric("Heizschlüssel UG P2", f"{pug2*100:.2f} %")
    c3.metric("COP P1", f"{cop1:.2f}", "plausibel" if 1.5 <= cop1 <= 6 else "prüfen")
    c4.metric("COP Leer+P2", f"{cop2:.2f}", "plausibel" if 1.5 <= cop2 <= 6 else "prüfen")

    st.subheader("Zählerstände")

    def _fmt(m, tag):
        return f"{m.staende[tag]:.3f}" if tag in m.staende else "–"

    rows = []
    for m in cfg.METERS.values():
        rows.append({
            "Zähler": m.beschreibung, "Nr.": m.serial_no, "Einheit": m.einheit,
            "Feb 2024": _fmt(m, cfg.STICHTAG_START),
            "Mai 2025": _fmt(m, cfg.STICHTAG_MITTE),
            "Jun 2026": _fmt(m, cfg.STICHTAG_ENDE),
        })
    st.dataframe(rows, width="stretch", hide_index=True)
    st.info("Die März-2026-WMZ-Ablesung wurde verworfen (COP-Prüfung ergab ein "
            "falsches Register). Es wird nur mit den drei belastbaren Stichtagen "
            "gerechnet.")

    OUTPUT.mkdir(exist_ok=True)
    vpfad = pdf.verbrauchsuebersicht_pdf(OUTPUT / "NK_Verbrauchsuebersicht.pdf")
    st.download_button("📄 Verbrauchsübersicht-PDF", Path(vpfad).read_bytes(),
                       file_name="NK_Verbrauchsuebersicht.pdf", mime="application/pdf")


# ---------------------------------------------------------------------------
# ℹ️ Status
# ---------------------------------------------------------------------------
else:
    st.header("ℹ️ Status & Stammdaten")
    st.write(f"**Objekt:** {cfg.OBJEKT['adresse']}")
    st.write(f"**UG-Anteil:** {cfg.UG_ANTEIL*100:.2f} %  ·  "
             f"**Strompreis:** {_eur(cfg.STROMPREIS_EUR_KWH)}/kWh")
    st.write(f"**Datenbank:** `{DB_PATH}`")
    st.write(f"**OCR-Backends:** {', '.join(backends) if backends else 'keine'}")
    st.divider()
    st.write("**Kostenparameter**")
    st.table([
        {"Parameter": "Wassertarif 2024", "Wert": f"{cfg.WASSERTARIF_EUR_M3[2024]:.2f} €/m³"},
        {"Parameter": "Wassertarif 2025/26", "Wert": f"{cfg.WASSERTARIF_EUR_M3[2025]:.2f} €/m³"},
        {"Parameter": "WW-Heizenergie", "Wert": f"{cfg.WW_ENERGIE_EUR_M3:.5f} €/m³"},
        {"Parameter": "Gebäudeversicherung", "Wert": f"{_eur(cfg.GEBAEUDEVERSICHERUNG_EUR_MONAT)}/Mon"},
        {"Parameter": "Grundsteuer B", "Wert": f"{_eur(cfg.GRUNDSTEUER_EUR_MONAT)}/Mon"},
        {"Parameter": "EnBW Grundpreis/Monat", "Wert": f"{_eur(cfg.ENBW_GRUNDPREIS_EUR_MONAT)}"},
    ])

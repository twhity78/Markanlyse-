"""Streamlit-Oberfläche: Zähler-Ablesung per Foto + NK-Abrechnung.

Teinacher Str. 4, 75387 Neubulach.

Start lokal:
    streamlit run streamlit_app.py

Gemeinsamer Cloud-Betrieb (beide Parteien, jederzeit, von überall):
    Mit DATABASE_URL (Supabase/Postgres) in den Secrets läuft die App auf
    einer geteilten Datenbank statt der lokalen SQLite-Datei. Zählerstände,
    Belege UND die zugehörigen Fotos werden direkt in der Datenbank
    gespeichert (nicht als lokale Datei), damit beide Parteien sie von
    jedem Gerät aus sehen und ergänzen können – siehe README.md.

Der Zählerstand bzw. Rechnungsbetrag wird – sofern ein OCR-Backend
verfügbar ist (Claude Vision oder Tesseract) – automatisch vorgeschlagen
und vom Nutzer bestätigt.
"""

from __future__ import annotations

import hmac
import os
from datetime import date
from pathlib import Path

import streamlit as st

from nk_abrechnung import config as cfg
from nk_abrechnung import engine as e
from nk_abrechnung import database, db_backend, handbuch, media, ocr, pdf

BASE = Path(__file__).parent
OUTPUT = BASE / "output"
DB_PATH = OUTPUT / "nk_teinacher.db"  # nur relevant im lokalen SQLite-Modus


def _eur(v: float) -> str:
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


@st.cache_resource
def get_db_path() -> str:
    OUTPUT.mkdir(exist_ok=True)
    return str(database.build(DB_PATH))


def con():
    return database.connect(get_db_path())


st.set_page_config(page_title="NK-Abrechnung Teinacher Str. 4",
                   page_icon="🏠", layout="wide")


# ---------------------------------------------------------------------------
# Passwortschutz (nur aktiv, wenn ein Passwort konfiguriert ist)
# ---------------------------------------------------------------------------
def _configured_password() -> str | None:
    """Passwort aus st.secrets (Cloud) oder Umgebungsvariable, sonst None."""
    try:
        if "app_password" in st.secrets:
            return str(st.secrets["app_password"])
    except Exception:
        pass
    return os.environ.get("NK_APP_PASSWORD")


def check_password() -> bool:
    """Blockt die App mit einer Passwortabfrage, falls ein Passwort gesetzt ist.

    Ohne konfiguriertes Passwort (lokaler Betrieb) läuft die App ungeschützt.
    """
    pw = _configured_password()
    if not pw:
        return True
    if st.session_state.get("auth_ok"):
        return True

    st.title("🏠 NK-Abrechnung")
    st.caption(cfg.OBJEKT["adresse"])
    eingabe = st.text_input("Passwort", type="password",
                            placeholder="Zugang zur Abrechnung")
    if eingabe:
        if hmac.compare_digest(eingabe, pw):
            st.session_state["auth_ok"] = True
            st.rerun()
        else:
            st.error("Falsches Passwort.")
    st.stop()


check_password()

st.sidebar.title("🏠 NK-Abrechnung")
st.sidebar.caption(cfg.OBJEKT["adresse"])
seite = st.sidebar.radio(
    "Navigation",
    ["📷 Zähler ablesen", "📋 Ablesungen", "🗂️ Belege",
     "🧾 Abrechnung", "📊 Verbrauch & COP", "ℹ️ Status"],
)

KATEGORIE_LABEL = {
    "strom": "⚡ Strom (EnBW)",
    "wasser": "💧 Wasser/Abwasser",
    "versicherung": "🛡️ Gebäudeversicherung",
    "grundsteuer": "🏛️ Grundsteuer B",
    "niederschlag": "🌧️ Niederschlagswasser",
    "sonstiges": "📄 Sonstiges",
}

backends = ocr.available_backends()
if backends:
    st.sidebar.success("OCR aktiv: " + ", ".join(backends))
else:
    st.sidebar.info("Kein OCR-Backend – Werte manuell eingeben.\n\n"
                    "Aktivierbar über `ANTHROPIC_API_KEY` (Claude Vision) "
                    "oder Installation von Tesseract.")

if db_backend.database_url():
    st.sidebar.success("☁️ Geteilte Cloud-Datenbank aktiv – beide Parteien "
                       "sehen dieselben Daten, dauerhaft gespeichert.")
else:
    st.sidebar.warning("💾 Lokale Datenbank (SQLite) – nur auf diesem Rechner. "
                       "Für geteilten Zugriff beider Parteien: DATABASE_URL "
                       "(Supabase) in den Secrets setzen, siehe README.")


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
        erfasser = st.selectbox("Erfasst von", database.ERFASSER_OPTIONEN)
    with col2:
        quelle = st.radio("Foto-Quelle", ["Hochladen", "Kamera"], horizontal=True)
        if quelle == "Kamera":
            bild = st.camera_input("Zähler fotografieren")
        else:
            bild = st.file_uploader("Zählerfoto", type=["jpg", "jpeg", "png"])

    vorschlag = st.session_state.get("ocr_value")
    foto_bytes = foto_name = foto_mime = None

    if bild is not None:
        st.image(bild, caption="Zählerfoto", width=360)
        foto_bytes, foto_mime = media.compress_image(bild.getvalue())
        foto_name = Path(getattr(bild, "name", "foto.jpg")).name

        if backends and st.button("🔍 Zählerstand per OCR erkennen"):
            with st.spinner("OCR läuft …"):
                res = ocr.read_meter(foto_bytes, foto_mime)
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
                       f"({letzte['value']} am {letzte['date']}, "
                       f"erfasst von {letzte['recorded_by'] or '–'}). Bitte prüfen.")

    if st.button("💾 Ablesung speichern", type="primary", disabled=(wert <= 0)):
        database.add_reading(c, meter["id"], ablesedatum.isoformat(), float(wert),
                             recorded_by=erfasser, photo_filename=foto_name,
                             photo_mime=foto_mime, photo_data=foto_bytes)
        st.session_state.pop("ocr_value", None)
        st.success(f"Gespeichert: {meter['description']} = {wert} {meter['unit']} "
                   f"({ablesedatum.isoformat()}, erfasst von {erfasser})")
    c.close()


# ---------------------------------------------------------------------------
# 📋 Ablesungen
# ---------------------------------------------------------------------------
elif seite == "📋 Ablesungen":
    st.header("📋 Erfasste Ablesungen")
    st.caption("Sichtbar für beide Parteien – unabhängig davon, wer die "
               "Ablesung erfasst hat.")
    c = con()
    readings = database.list_readings(c)
    if not readings:
        st.info("Noch keine Ablesungen erfasst.")
    else:
        tabelle = [{"Datum": r["date"], "Zähler": r["description"],
                    "Nr.": r["serial_no"], "Wert": r["value"],
                    "Einheit": r["unit"], "Erfasst von": r["recorded_by"] or "–",
                    "Foto": "📎" if r["has_photo"] else ""}
                   for r in readings]
        st.dataframe(tabelle, width="stretch", hide_index=True)

        mit_foto = [r for r in readings if r["has_photo"]]
        if mit_foto:
            st.subheader("Fotonachweise")
            cols = st.columns(4)
            for i, r in enumerate(mit_foto):
                foto = database.get_reading_photo(c, r["id"])
                if not foto:
                    continue
                _name, _mime, data = foto
                with cols[i % 4]:
                    st.image(data,
                             caption=f"{r['description']} · {r['date']} · {r['recorded_by'] or ''}",
                             width="stretch")
    c.close()


# ---------------------------------------------------------------------------
# 🗂️ Belege (Eingangsrechnungen: Strom, Wasser, Versicherung, …)
# ---------------------------------------------------------------------------
elif seite == "🗂️ Belege":
    st.header("🗂️ Rechnungsbelege")
    st.caption("Foto- oder PDF-Nachweise der aktuellen Eingangsrechnungen "
               "(Strom, Wasser, Versicherung, Grundsteuer, Niederschlagswasser). "
               "Viele Rechnungen gehen bei Christine Weis ein – hier erfasst, "
               "sind sie sofort auch für die andere Partei dokumentiert.")
    c = con()

    tab_neu, tab_liste = st.tabs(["➕ Beleg erfassen", "📚 Belegübersicht"])

    with tab_neu:
        col1, col2 = st.columns(2)
        with col1:
            kat = st.selectbox("Kategorie", database.RECEIPT_CATEGORIES,
                               format_func=lambda k: KATEGORIE_LABEL.get(k, k))
            lieferant = st.text_input("Lieferant / Aussteller",
                                      placeholder="z.B. EnBW, Gemeinde, Versicherer")
            rechnungsdatum = st.date_input("Rechnungsdatum", value=date.today())
            erfasser = st.selectbox("Erfasst von", database.ERFASSER_OPTIONEN,
                                    key="beleg_erfasser")
        with col2:
            p_von = st.date_input("Abrechnungszeitraum von", value=None)
            p_bis = st.date_input("Abrechnungszeitraum bis", value=None)
            notiz = st.text_input("Notiz (optional)")

        beleg = st.file_uploader("Beleg (Foto oder PDF)",
                                 type=["jpg", "jpeg", "png", "pdf"])
        betrag_vorschlag = st.session_state.get("beleg_amount")
        beleg_bytes = beleg_mime = None

        if beleg is not None:
            ist_bild = media.is_image(beleg.name, beleg.type)
            if ist_bild:
                beleg_bytes, beleg_mime = media.compress_image(beleg.getvalue())
                st.image(beleg, caption="Beleg", width=360)
                if backends and st.button("🔍 Betrag per OCR erkennen"):
                    with st.spinner("OCR läuft …"):
                        res = ocr.read_amount(beleg_bytes, beleg_mime)
                    if res.value is not None:
                        st.session_state["beleg_amount"] = res.value
                        betrag_vorschlag = res.value
                        st.success(f"Erkannt ({res.backend}): {res.value} €")
                    else:
                        st.warning(res.note or "Kein Betrag erkannt – bitte manuell eingeben.")
                    if res.raw_text:
                        st.caption(f"Rohtext: {res.raw_text}")
            else:
                beleg_bytes = beleg.getvalue()
                beleg_mime = "application/pdf"
                st.info(f"📄 PDF bereit zum Speichern: {beleg.name}")

        betrag = st.number_input(
            "Rechnungsbetrag (€)",
            value=float(betrag_vorschlag) if betrag_vorschlag is not None else 0.0,
            step=0.01, format="%.2f",
        )

        if st.button("💾 Beleg speichern", type="primary",
                     disabled=(beleg_bytes is None)):
            database.add_receipt(
                c, category=kat, file_name=beleg.name, file_data=beleg_bytes,
                file_mime=beleg_mime, supplier=lieferant or None,
                amount=float(betrag) if betrag > 0 else None,
                invoice_date=rechnungsdatum.isoformat(),
                period_from=p_von.isoformat() if p_von else None,
                period_to=p_bis.isoformat() if p_bis else None,
                recorded_by=erfasser, note=notiz or None,
            )
            st.session_state.pop("beleg_amount", None)
            st.success(f"Beleg gespeichert: {KATEGORIE_LABEL.get(kat, kat)}"
                       + (f" · {_eur(betrag)}" if betrag > 0 else "")
                       + f" · erfasst von {erfasser}")

    with tab_liste:
        belege = database.list_receipts(c)
        if not belege:
            st.info("Noch keine Belege erfasst.")
        else:
            summen: dict[str, float] = {}
            for b in belege:
                summen[b["category"]] = summen.get(b["category"], 0.0) + (b["amount"] or 0.0)
            st.subheader("Summen je Kategorie")
            st.table([{"Kategorie": KATEGORIE_LABEL.get(k, k), "Summe": _eur(v),
                       "Belege": sum(1 for b in belege if b["category"] == k)}
                      for k, v in summen.items()])

            st.subheader("Alle Belege")
            for b in belege:
                titel = (f"{KATEGORIE_LABEL.get(b['category'], b['category'])} · "
                         f"{b['supplier'] or '—'} · "
                         f"{_eur(b['amount']) if b['amount'] else 'Betrag offen'} · "
                         f"{b['invoice_date'] or ''}")
                with st.expander(titel):
                    zeitraum = (f"{b['period_from']} – {b['period_to']}"
                                if b["period_from"] else "—")
                    st.write(f"**Zeitraum:** {zeitraum}")
                    st.write(f"**Erfasst von:** {b['recorded_by'] or '–'}")
                    if b["note"]:
                        st.write(f"**Notiz:** {b['note']}")
                    if st.button("📂 Datei anzeigen", key=f"show_{b['id']}"):
                        datei = database.get_receipt_file(c, b["id"])
                        if datei:
                            fname, fmime, fdata = datei
                            if (fmime or "").startswith("image/"):
                                st.image(fdata, width=360)
                            else:
                                st.download_button(
                                    "📄 PDF öffnen", fdata, file_name=fname,
                                    mime=fmime or "application/pdf",
                                    key=f"dl_{b['id']}")
                    if st.button("🗑️ Beleg löschen", key=f"del_{b['id']}"):
                        database.delete_receipt(c, b["id"])
                        st.rerun()
    c.close()


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

    st.subheader(f"Eigentümer-intern ({cfg.NEUER_EIGENTUEMER_NAME} ↔ {cfg.ZWEITE_PARTEI_NAME})")
    st.caption("Historische Positionen (P1, Leerstand, P2) fielen noch in die "
              "Eigentumszeit von Thomas Weis; künftige Positionen betreffen "
              "den neuen Eigentümer.")
    es = e.eigentuemer_zwischenstand()
    st.table([{"Position": b, "Betrag": _eur(v)} for b, v in es.positionen]
             + [{"Position": "Zwischensaldo", "Betrag": _eur(es.zwischensaldo)}])
    st.caption(f"Kulanz WW-EG erlassen: {_eur(es.ww_eg_erlassen)}")
    for p in es.offene_punkte:
        st.warning("Offen: " + p)
    epfad = pdf.eigentuemer_pdf(es, OUTPUT / "NK_Eigentuemer_Zwischenstand.pdf")
    st.download_button("📄 Eigentümer-PDF", Path(epfad).read_bytes(),
                       file_name="NK_Eigentuemer_Zwischenstand.pdf",
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
    st.write(f"**Eigentümer:** {cfg.NEUER_EIGENTUEMER_NAME} / {cfg.ZWEITE_PARTEI_NAME}")
    if db_backend.database_url():
        st.write("**Datenbank:** ☁️ Postgres/Supabase (geteilt, dauerhaft)")
    else:
        st.write(f"**Datenbank:** 💾 lokal `{DB_PATH}`")
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
    st.divider()
    st.write("**Übergabe-Handbuch**")
    st.caption("Ausführliche Schritt-für-Schritt-Anleitung (Einrichtung, tägliche "
              "Nutzung, jährliche Abrechnung, offene Punkte, Problembehebung).")
    OUTPUT.mkdir(exist_ok=True)
    hpfad = handbuch.handbuch_pdf(OUTPUT / "Handbuch_Uebergabe.pdf")
    st.download_button("📘 Handbuch herunterladen (PDF)", Path(hpfad).read_bytes(),
                       file_name="Handbuch_Uebergabe.pdf", mime="application/pdf")

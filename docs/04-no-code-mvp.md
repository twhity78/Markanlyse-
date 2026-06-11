# No-Code MVP: Marktanalyse als Service ohne Programmierung

**Voraussetzung:** Mindestens 1 validierter Interessent aus dem
[Validierungs-Sprint](03-validierungs-sprint.md).

**Ziel:** Innerhalb von 1–2 Wochen die ersten bezahlten Reports liefern —
mit Werkzeugen, die du heute schon bedienen kannst.

---

## Der Werkzeugkasten (alles ohne Code)

| Aufgabe | Werkzeug | Kosten |
|---------|----------|--------|
| Analyse & Texterstellung | Claude (claude.ai, Pro-Abo empfohlen) | ~20 €/Monat |
| Kunden-Input erfassen | Google Forms oder Typeform | 0 € |
| Report-Layout | Google Docs Vorlage oder Canva | 0 € |
| Auslieferung | PDF per E-Mail | 0 € |
| Bezahlung | Rechnung + Überweisung (am Anfang reicht das) | 0 € |
| Kundenverwaltung | Eine simple Tabelle (Google Sheets) | 0 € |

**Gesamtkosten: ~20 €/Monat.** Das deckt sich mit der Evaluierungs-Matrix
aus dem Quelldokument ($20–100/Monat für das 1-Personen-Business).

---

## Der Produktionsprozess (pro Report)

### 1. Kunden-Briefing einholen (Formular)

Frage im Formular ab:
- Firma, Branche, Region
- Die 3 wichtigsten Wettbewerber aus Kundensicht
- Die eine Entscheidung, die der Report unterstützen soll
- Gewünschter Rhythmus (einmalig / monatlich)

### 2. Recherche & Analyse mit Claude

Baue dir eine **wiederverwendbare Prompt-Vorlage** (dein eigentliches
Betriebskapital!). Starte mit der Vorlage aus dem
[Validierungs-Sprint, Tag 2–3](03-validierungs-sprint.md) und verfeinere
sie nach jedem Report.

**Wichtigste Regel:** Jede Zahl und jede Wettbewerber-Aussage, die in den
Report geht, prüfst du selbst nach (Website des Wettbewerbers, Google,
Branchenverbände, Statistisches Bundesamt / destatis, IHK-Berichte).
KI liefert Struktur und Entwurf — **du lieferst die Verlässlichkeit.**
Das ist der Grund, warum Kunden dich bezahlen statt selbst zu prompten.

### 3. Veredeln & ausliefern

- Entwurf in deine Report-Vorlage übertragen (einheitliches Layout = Marke)
- Executive Summary selbst schreiben/schärfen — das liest der Chef zuerst
- Als PDF senden, mit 2–3 Sätzen persönlicher Einordnung in der E-Mail

### 4. Feedback-Schleife

Nach jedem Report eine Frage an den Kunden:
*"Welcher Teil war am nützlichsten — und was hat gefehlt?"*
Antworten fließen in die Prompt-Vorlage ein.

---

## Preisgestaltung für die Pilotphase

| Stufe | Angebot | Preis |
|-------|---------|-------|
| Pilot (Kunde 1–3) | Erster Report stark vergünstigt gegen ausführliches Feedback + Erlaubnis als Referenz | 99–199 € |
| Einzelreport | Einmalige Markt-/Wettbewerbsanalyse | 300–800 € |
| **Retainer (Ziel)** | Monatlicher Report + 30-Min-Call | **300–500 €/Monat** |

> **Retainer ist das Ziel** (siehe [Analyse, Phase 3](01-analyse-14-pfade.md)):
> 10 Retainer-Kunden à 400 € = 4.000 €/Monat wiederkehrend — als Einzelperson
> mit wenigen Stunden Aufwand pro Kunde, sobald der Prozess steht.

---

## Wann auf das Code-MVP umsteigen?

Steige erst auf ein selbstgebautes Tool um ([Roadmap](05-roadmap.md)), wenn
**mindestens zwei** dieser Signale da sind:

- [ ] 3+ zahlende Kunden
- [ ] Du verbringst > 2 Stunden pro Report mit mechanischer Arbeit
      (Copy-Paste, Formatieren), die sich automatisieren ließe
- [ ] Kunden fragen nach Selbstbedienung ("Kann ich das selbst abrufen?")
- [ ] Der Prozess ist stabil — du änderst die Prompt-Vorlage kaum noch

**Vorher zu automatisieren ist die klassische Falle:** Man baut Software
für einen Prozess, den noch niemand kaufen wollte.

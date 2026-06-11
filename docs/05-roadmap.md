# Roadmap: Von der Exploration zur KI-Agentur

Gesamtfahrplan für "Markanlyse" — angelehnt an die 3 Phasen des
Quelldokuments, aber mit Validierung vor jedem Ausbau-Schritt.

---

## Überblick

```
Exploration          Validierung         No-Code MVP         Code-MVP            KI-Agentur
(diese Woche)   →    (Woche 1)      →    (Woche 2–4)    →    (Monat 2–3)    →    (Monat 4+)
Nische finden        Kaufzusagen         Erste bezahlte      Web-Tool +          Retainer-Kunden
                     einholen            Reports             Automatisierung     skalieren
```

Jeder Pfeil hat ein **Gate** — erst weitergehen, wenn das Kriterium erfüllt ist.

---

## Etappe 1: Exploration ✅ (in Arbeit)

- [x] Quelldokument analysiert → [01-analyse-14-pfade.md](01-analyse-14-pfade.md)
- [ ] Nischenfinder durchgearbeitet → [02-nischenfinder.md](02-nischenfinder.md)
- [ ] 2–3 Nischen-Kandidaten dokumentiert

**Gate:** Kandidat A mit erstem möglichen Kunden benannt.

## Etappe 2: Validierungs-Sprint (Woche 1)

- [ ] 10er-Zielliste erstellt
- [ ] Demo-Report mit Claude erstellt
- [ ] 5+ Gespräche geführt
- [ ] Sprint-Protokoll ausgefüllt → [03-validierungs-sprint.md](03-validierungs-sprint.md)

**Gate:** Mindestens 1 konkrete Kaufzusage mit Betrag.

## Etappe 3: No-Code MVP (Woche 2–4)

- [ ] Report-Vorlage + Prompt-Vorlage gebaut
- [ ] Pilotkunden 1–3 beliefert (99–199 €)
- [ ] Feedback eingearbeitet, Preis auf Normalniveau angehoben

**Gate:** 3 zahlende Kunden ODER > 2 h mechanische Arbeit pro Report
(siehe Kriterien in [04-no-code-mvp.md](04-no-code-mvp.md)).

## Etappe 4: Code-MVP (Monat 2–3)

Jetzt erst wird dieses Repo zum Software-Projekt. Geplanter Stack
(wird gemeinsam Schritt für Schritt gebaut, lernfreundlich):

- **Next.js** — Web-App (Formular rein, Report raus)
- **Claude API** (Anthropic SDK) — Analyse-Engine mit deiner erprobten Prompt-Vorlage
- **Vercel** — Hosting (kostenloser Einstieg)

Geplante Struktur:

```
src/
  app/
    page.tsx                 # Eingabeformular (Firma, Branche, Wettbewerber)
    api/analyze/route.ts     # Claude-API-Aufruf mit Prompt-Vorlage
  components/
    AnalysisReport.tsx       # Report-Darstellung + PDF-Export
```

- [ ] Projekt-Setup (Next.js + Anthropic SDK)
- [ ] Prompt-Vorlage aus Etappe 3 als API-Endpunkt
- [ ] Report-Ausgabe als Web-Ansicht + PDF
- [ ] Interne Nutzung: Du produzierst Reports in Minuten statt Stunden

**Gate:** Tool spart dir nachweislich > 50 % der Zeit pro Report.

## Etappe 5: KI-Agentur & Retainer-Skalierung (Monat 4+)

Das Phase-3-Modell aus dem Quelldokument:

- [ ] Retainer-Angebot standardisieren (300–500 €/Monat: Report + Call)
- [ ] 10 Retainer-Kunden = ~4.000 €/Monat wiederkehrend
- [ ] Optional: Kunden-Self-Service (Login, eigene Reports abrufen)
- [ ] Optional: White-Label für Unternehmensberater (deren Marke, deine Engine)
- [ ] Langfristig: Infrastruktur-Partner für Mittelstand (Path 14)

---

## Grundsätze (aus der Analyse abgeleitet)

1. **Verkaufen vor Bauen.** Jede Ausbaustufe braucht zahlende Nachfrage als Gate.
2. **B2B, nicht B2C.** Firmen zahlen für gelöste Probleme, Konsumenten für Unterhaltung.
3. **Retainer schlägt Einzelauftrag.** Wiederkehrender Umsatz ist das Ziel jeder Etappe.
4. **Die KI ist der Entwurf, du bist die Qualität.** Geprüfte Verlässlichkeit ist
   der Burggraben gegen "der Kunde prompted selbst".
5. **Zeit-Entkopplung als Nordstern.** Jede Etappe reduziert die Stunden pro Euro Umsatz.

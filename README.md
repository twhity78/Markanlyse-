# Marktanalyse

Automatischer Marktberichts-Generator für **Aktien, Krypto, Immobilien und Branchenanalyse**. Erzeugt wöchentlich strukturierte Berichte als Markdown und HTML.

## Funktionen

- **📈 Aktienmärkte** – Kurse, Tages-/Wochen-/Monatsveränderung, 52-Wochen-Hoch/-Tief mit Sparklines
- **🪙 Kryptomärkte** – Bitcoin, Ethereum, Solana und mehr via CoinGecko
- **🏠 Immobilienmarkt** – Preise pro m², YoY- und 5-Jahres-Entwicklung für deutsche Regionen
- **🏭 Branchenanalyse** – Sektorkennzahlen und Wettbewerbsprofile

## Berichtsformat

Jeder Bericht wird als **Markdown** und **HTML** (mit Inline-Sparklines) gespeichert:

```
reports/
  YYYY-MM-DD/
    report.md
    report.html
  latest.md
  latest.html
```

## Schnellstart

```bash
npm install
npm run generate       # Bericht jetzt erstellen
```

Den aktuellen Bericht finden Sie danach in `reports/latest.html`.

## Automatisierung via GitHub Actions

Der Workflow `.github/workflows/report.yml` läuft **jeden Montag um 06:00 UTC** und kann jederzeit manuell über _Actions → Marktbericht generieren → Run workflow_ gestartet werden.

Der Bericht wird automatisch nach `reports/` committet und als GitHub-Artifact (90 Tage) gespeichert.

## Watchlists anpassen

Bearbeiten Sie `market-config.json`:

```json
{
  "stocks": [
    { "symbol": "aapl.us", "name": "Apple", "currency": "USD" }
  ],
  "crypto": [
    { "id": "bitcoin", "name": "Bitcoin", "vsCurrency": "eur" }
  ],
  "realEstate": { "regions": ["Berlin", "München"] },
  "industry": {
    "sector": "Meine Branche",
    "competitors": [
      { "name": "Firma XY", "ticker": "xy.de", "notes": "Kurznotiz" }
    ]
  }
}
```

Aktien-Symbole folgen dem [stooq.com-Format](https://stooq.com) (z. B. `aapl.us`, `sap.de`, `^dax`).
Krypto-IDs folgen [CoinGecko](https://www.coingecko.com/api/documentation) (z. B. `bitcoin`, `ethereum`).

## Datenquellen

| Bereich | Quelle | Hinweis |
|---------|--------|---------|
| Aktien | stooq.com | Kostenlos, kein API-Key |
| Krypto | CoinGecko API v3 | Kostenlos, kein API-Key |
| Immobilien | Destatis-Schätzungen | Statische Beispieldaten; Update via `data/fixtures/real-estate.json` |
| Branche | Konfigurationsdatei | Qualitative Notizen in `market-config.json` |

> **Hinweis:** Im lokalen Betrieb (kein API-Zugang) werden automatisch Beispieldaten aus `data/fixtures/` verwendet — Berichte kennzeichnen dies sichtbar. Auf GitHub Actions laufen Live-Daten.

## Entwicklung

```bash
npm run typecheck      # TypeScript-Prüfung
npm run lint           # ESLint
npm test               # Tests (vitest)
npm run check          # Alle drei zusammen
```

## Erweiterungsmöglichkeiten

- **PDF-Export**: `md-to-pdf` oder Puppeteer
- **E-Mail-Versand**: GitHub Actions + SMTP-Secret
- **Weitere Regionen**: Einträge in `data/fixtures/real-estate.json` ergänzen
- **Live-Immobiliendaten**: Adapter in `src/sources/realEstate.ts` erweitern
- **Historien-Indexseite**: Übersicht aller vergangenen Berichte als HTML

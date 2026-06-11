import { describe, it, expect } from "vitest";
import { renderMarkdown } from "../src/render/markdown.js";
import type { Report } from "../src/types.js";
import type { IndustryData } from "../src/sources/industry.js";

const sampleReport: Report = {
  generatedAt: "2026-06-10T06:00:00.000Z",
  stocks: {
    title: "Aktienmärkte",
    meta: { source: "sample", fetchedAt: "2026-06-10T06:00:00.000Z" },
    data: [
      {
        symbol: "^spx",
        name: "S&P 500",
        currency: "USD",
        price: 6378,
        change1d: 0.2,
        change7d: 1.1,
        change30d: 3.5,
        high52w: 6400,
        low52w: 5200,
        history: [
          { date: "2026-06-09", close: 6365 },
          { date: "2026-06-10", close: 6378 },
        ],
      },
    ],
  },
  crypto: {
    title: "Kryptomärkte",
    meta: { source: "sample", fetchedAt: "2026-06-10T06:00:00.000Z" },
    data: [
      {
        symbol: "bitcoin",
        name: "Bitcoin",
        currency: "EUR",
        price: 149500,
        change1d: 1.02,
        change7d: 2.5,
        change30d: 10.2,
        high52w: 155000,
        low52w: 85000,
        marketCap: 1820000000000,
        volume: 38500000000,
        history: [
          { date: "2026-06-09", close: 147000 },
          { date: "2026-06-10", close: 149500 },
        ],
      },
    ],
  },
  realEstate: {
    title: "Immobilienmarkt",
    meta: { source: "sample", fetchedAt: "2026-06-10T06:00:00.000Z" },
    data: [
      { region: "Berlin", pricePerSqm: 5450, changeYoY: 4.8, change5y: 42.1, year: 2025 },
    ],
  },
  industry: {
    title: "Branchen- & Wettbewerbsanalyse",
    meta: { source: "sample", fetchedAt: "2026-06-10T06:00:00.000Z" },
    data: {
      sector: "Software & Cloud",
      sectorStats: {
        globalMarketSizeUsdBn: 920,
        yoyGrowthPct: 14.2,
        topTrends: ["KI-Integration"],
      },
      competitors: [
        { name: "SAP", ticker: "sap.de", notes: "Marktführer ERP" },
      ],
    } as IndustryData,
  },
};

describe("renderMarkdown", () => {
  it("enthält Berichtstitel", () => {
    const md = renderMarkdown(sampleReport);
    expect(md).toContain("Marktbericht");
  });

  it("enthält alle vier Abschnitte", () => {
    const md = renderMarkdown(sampleReport);
    expect(md).toContain("Aktienmärkte");
    expect(md).toContain("Kryptomärkte");
    expect(md).toContain("Immobilienmarkt");
    expect(md).toContain("Wettbewerb");
  });

  it("zeigt Beispieldaten-Hinweis", () => {
    const md = renderMarkdown(sampleReport);
    expect(md).toContain("Beispieldaten");
  });

  it("enthält S&P 500 Daten", () => {
    const md = renderMarkdown(sampleReport);
    expect(md).toContain("S&P 500");
    expect(md).toContain("6.378");
  });

  it("enthält Bitcoin mit Marktkapitalisierung", () => {
    const md = renderMarkdown(sampleReport);
    expect(md).toContain("Bitcoin");
    expect(md).toContain("Mrd.");
  });
});

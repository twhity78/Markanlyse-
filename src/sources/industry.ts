import { loadFixture } from "./fetchWithFallback.js";
import type { Competitor, DomainSection } from "../types.js";
import type { MarketConfig } from "../config.js";

interface IndustryFixture {
  sector: string;
  sectorStats: {
    globalMarketSizeUsdBn: number;
    yoyGrowthPct: number;
    topTrends: string[];
  };
  competitors: Array<{ name: string; ticker?: string; notes: string }>;
}

export interface IndustryData {
  sector: string;
  sectorStats: IndustryFixture["sectorStats"];
  competitors: Competitor[];
}

export function fetchIndustry(config: MarketConfig["industry"]): DomainSection<IndustryData> {
  const fixture = loadFixture<IndustryFixture>("industry");

  const competitors: Competitor[] = config.competitors.map((c) => ({
    name: c.name,
    ticker: c.ticker,
    notes: c.notes,
  }));

  return {
    title: "Branchen- & Wettbewerbsanalyse",
    meta: { source: "sample", fetchedAt: new Date().toISOString() },
    data: {
      sector: config.sector,
      sectorStats: fixture.sectorStats,
      competitors,
    },
  };
}
